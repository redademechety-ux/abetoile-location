from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
import asyncio
from enum import Enum
import base64
from pdf_generator import PDFInvoiceGenerator
from accounting import FrenchAccounting, AccountingEntry
from services.mailgun_service import mailgun_service, EmailRequest
from services.insee_service import insee_service, CompanyInfo

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# PDF and Accounting services
pdf_generator = PDFInvoiceGenerator()
accounting_system = FrenchAccounting()

# Create the main app
app = FastAPI(title="Abetoile Location Management", version="1.0.0")

# Create API router
api_router = APIRouter(prefix="/api")

# Enums
class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class RentalPeriod(str, Enum):
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"

class VehicleType(str, Enum):
    CAR = "car"
    VAN = "van"
    TRUCK = "truck"
    MOTORCYCLE = "motorcycle"
    OTHER = "other"

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    full_name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str
    contact_name: str
    email: EmailStr
    phone: str
    address: str
    city: str
    postal_code: str
    country: str = "France"
    vat_rate: float = 20.0
    vat_number: Optional[str] = None
    rcs_number: Optional[str] = None
    license_documents: List[str] = []  # Base64 encoded documents
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class ClientCreate(BaseModel):
    company_name: str
    contact_name: str
    email: EmailStr
    phone: str
    address: str
    city: str
    postal_code: str
    country: str = "France"
    vat_rate: float = 20.0
    vat_number: Optional[str] = None
    rcs_number: Optional[str] = None

class Vehicle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: VehicleType
    brand: str
    model: str
    license_plate: str
    first_registration: datetime
    technical_control_expiry: datetime
    insurance_company: str
    insurance_contract: str
    insurance_amount: float
    insurance_expiry: datetime
    registration_documents: List[str] = []  # Base64 encoded documents
    attachments: List[Dict[str, str]] = []  # {"filename": "...", "data": "...", "description": "..."}
    daily_rate: float
    accounting_account: str = "706000"  # Default sales account
    is_available: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VehicleCreate(BaseModel):
    type: VehicleType
    brand: str
    model: str
    license_plate: str
    first_registration: datetime
    technical_control_expiry: datetime
    insurance_company: str
    insurance_contract: str
    insurance_amount: float
    insurance_expiry: datetime
    daily_rate: float
    accounting_account: str = "706000"

class OrderItem(BaseModel):
    vehicle_id: str
    quantity: int = 1
    daily_rate: float  # Prix journalier modifiable
    total_days: int = 1  # Nombre de jours calculé
    is_renewable: bool = False
    rental_period: Optional[RentalPeriod] = None
    rental_duration: Optional[int] = None
    start_date: Optional[datetime] = None  # Made optional for backward compatibility
    end_date: Optional[datetime] = None    # Made optional for backward compatibility
    item_total_ht: float = 0  # Total HT pour cet item

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    order_number: str
    items: List[OrderItem]
    deposit_amount: float = 0  # Montant de caution
    total_ht: float
    total_vat: float
    total_ttc: float
    deposit_vat: float = 0  # TVA sur la caution
    grand_total: float = 0  # Total TTC + caution
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str

class OrderCreate(BaseModel):
    client_id: str
    items: List[OrderItem]
    deposit_amount: float = 0

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_id: str
    amount: float
    payment_date: datetime
    payment_method: str  # "bank", "cash", "check", "card"
    reference: Optional[str] = None  # Référence bancaire, numéro chèque, etc.
    notes: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Invoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str
    order_id: str
    client_id: str
    invoice_date: datetime
    due_date: datetime
    items: List[OrderItem]
    deposit_amount: float = 0  # Montant de caution
    deposit_vat: float = 0  # TVA sur caution
    total_ht: float
    total_vat: float
    total_ttc: float
    grand_total: float = 0  # Total TTC + caution
    status: InvoiceStatus = InvoiceStatus.DRAFT
    amount_paid: float = 0  # Montant total payé
    remaining_amount: float = 0  # Montant restant à payer
    payment_date: Optional[datetime] = None  # Date du dernier paiement
    pdf_data: Optional[str] = None  # Base64 encoded PDF
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Settings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str = "Abetoile Location"
    company_address: str = ""
    company_phone: str = ""
    company_email: str = ""
    vat_rates: Dict[str, float] = {"standard": 20.0, "reduced": 10.0, "super_reduced": 5.5}
    payment_delays: Dict[str, int] = {"days": 30, "weeks": 7, "months": 30, "years": 365}
    reminder_periods: List[int] = [7, 15, 30]  # Days after due date
    reminder_templates: Dict[str, str] = {}
    accounting_accounts: Dict[str, str] = {
        "sales": "706000",
        "vat_standard": "445571",
        "vat_reduced": "445572"
    }
    mailgun_api_key: Optional[str] = None
    mailgun_domain: Optional[str] = None

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    filename: str
    content_type: str
    size: int
    label: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str

class MaintenanceType(str, Enum):
    REPAIR = "repair"  # Réparation
    MAINTENANCE = "maintenance"  # Entretien
    INSPECTION = "inspection"  # Contrôle
    OTHER = "other"  # Autre

class MaintenanceRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: str
    maintenance_type: MaintenanceType
    description: str  # Libellé
    maintenance_date: datetime
    amount_ht: float  # Montant HT
    vat_rate: float  # Taux de TVA (en pourcentage)
    vat_amount: float  # Montant TVA
    amount_ttc: float  # Montant TTC
    supplier: Optional[str] = None  # Fournisseur/Garage
    documents: List[str] = []  # IDs des documents PDF/JPG
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str

class MaintenanceRecordCreate(BaseModel):
    vehicle_id: str
    maintenance_type: MaintenanceType
    description: str
    maintenance_date: datetime
    amount_ht: float
    vat_rate: float
    supplier: Optional[str] = None
    notes: Optional[str] = None
# Auth functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)

# Helper functions
async def generate_order_number():
    count = await db.orders.count_documents({})
    return f"CMD{count + 1:06d}"

async def generate_invoice_number():
    count = await db.invoices.count_documents({})
    return f"FACT{count + 1:06d}"

def prepare_for_mongo(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, dict):
                data[key] = prepare_for_mongo(value)
            elif isinstance(value, list):
                data[key] = [prepare_for_mongo(item) if isinstance(item, dict) else item for item in value]
    return data

def parse_from_mongo(item):
    if isinstance(item, dict):
        for key, value in item.items():
            if isinstance(value, str) and 'T' in value:
                try:
                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass
    return item

# Auth endpoints
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    existing_email = await db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict()
    del user_dict['password']
    user_dict['hashed_password'] = hashed_password
    
    user = User(**user_dict)
    user_dict = prepare_for_mongo(user.dict())
    user_dict['hashed_password'] = hashed_password
    
    await db.users.insert_one(user_dict)
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user['hashed_password']):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user['username']})
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Client endpoints
@api_router.post("/clients", response_model=Client)
async def create_client(client_data: ClientCreate, current_user: User = Depends(get_current_user)):
    client = Client(**client_data.dict())
    client_dict = prepare_for_mongo(client.dict())
    await db.clients.insert_one(client_dict)
    return client

@api_router.get("/clients", response_model=List[Client])
async def get_clients(current_user: User = Depends(get_current_user)):
    clients = await db.clients.find({"is_active": True}).to_list(1000)
    return [Client(**parse_from_mongo(client)) for client in clients]

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str, current_user: User = Depends(get_current_user)):
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return Client(**parse_from_mongo(client))

@api_router.put("/clients/{client_id}", response_model=Client)
async def update_client(client_id: str, client_data: ClientCreate, current_user: User = Depends(get_current_user)):
    update_data = prepare_for_mongo(client_data.dict())
    result = await db.clients.update_one({"id": client_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    updated_client = await db.clients.find_one({"id": client_id})
    return Client(**parse_from_mongo(updated_client))

# Vehicle endpoints
@api_router.post("/vehicles", response_model=Vehicle)
async def create_vehicle(vehicle_data: VehicleCreate, current_user: User = Depends(get_current_user)):
    vehicle = Vehicle(**vehicle_data.dict())
    vehicle_dict = prepare_for_mongo(vehicle.dict())
    await db.vehicles.insert_one(vehicle_dict)
    return vehicle

@api_router.get("/vehicles", response_model=List[Vehicle])
async def get_vehicles(current_user: User = Depends(get_current_user)):
    vehicles = await db.vehicles.find().to_list(1000)
    return [Vehicle(**parse_from_mongo(vehicle)) for vehicle in vehicles]

@api_router.get("/vehicles/{vehicle_id}", response_model=Vehicle)
async def get_vehicle(vehicle_id: str, current_user: User = Depends(get_current_user)):
    vehicle = await db.vehicles.find_one({"id": vehicle_id})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return Vehicle(**parse_from_mongo(vehicle))

# Order endpoints
def calculate_days_between(start_date: datetime, end_date: datetime) -> int:
    """Calculate number of days between two dates"""
    delta = end_date - start_date
    return max(1, delta.days + 1)  # Include both start and end date

@api_router.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate, current_user: User = Depends(get_current_user)):
    # Get client to calculate VAT
    client = await db.clients.find_one({"id": order_data.client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Process each item and calculate totals
    processed_items = []
    total_ht = 0
    
    for item in order_data.items:
        # Calculate number of days for this item
        days = calculate_days_between(item.start_date, item.end_date)
        
        # Calculate item total
        item_total_ht = item.daily_rate * item.quantity * days
        
        # Create processed item
        processed_item = OrderItem(
            vehicle_id=item.vehicle_id,
            quantity=item.quantity,
            daily_rate=item.daily_rate,
            total_days=days,
            is_renewable=item.is_renewable,
            rental_period=item.rental_period,
            rental_duration=item.rental_duration,
            start_date=item.start_date,
            end_date=item.end_date,
            item_total_ht=item_total_ht
        )
        
        processed_items.append(processed_item)
        total_ht += item_total_ht
    
    # Calculate VAT and totals
    vat_rate = client['vat_rate'] / 100
    total_vat = total_ht * vat_rate
    total_ttc = total_ht + total_vat
    
    # Calculate deposit VAT and grand total
    deposit_vat = order_data.deposit_amount * vat_rate if order_data.deposit_amount > 0 else 0
    grand_total = total_ttc + order_data.deposit_amount + deposit_vat
    
    order_number = await generate_order_number()
    
    order = Order(
        client_id=order_data.client_id,
        order_number=order_number,
        items=processed_items,
        deposit_amount=order_data.deposit_amount,
        total_ht=total_ht,
        total_vat=total_vat,
        total_ttc=total_ttc,
        deposit_vat=deposit_vat,
        grand_total=grand_total,
        created_by=current_user.id
    )
    
    order_dict = prepare_for_mongo(order.dict())
    await db.orders.insert_one(order_dict)
    
    # Create initial invoice
    await create_invoice_from_order(order, client)
    
    return order

async def create_invoice_from_order(order: Order, client: dict):
    invoice_number = await generate_invoice_number()
    # Use the start date of the first item or current date
    invoice_date = datetime.now(timezone.utc)
    due_date = invoice_date + timedelta(days=30)  # Default 30 days
    
    invoice = Invoice(
        invoice_number=invoice_number,
        order_id=order.id,
        client_id=order.client_id,
        invoice_date=invoice_date,
        due_date=due_date,
        items=order.items,
        deposit_amount=order.deposit_amount,
        deposit_vat=order.deposit_vat,
        total_ht=order.total_ht,
        total_vat=order.total_vat,
        total_ttc=order.total_ttc,
        grand_total=order.grand_total,
        remaining_amount=order.grand_total,  # Initially, full amount is remaining
        status=InvoiceStatus.DRAFT
    )
    
    invoice_dict = prepare_for_mongo(invoice.dict())
    await db.invoices.insert_one(invoice_dict)
    
    # Generate accounting entries for the invoice
    try:
        settings = await db.settings.find_one()
        if not settings:
            settings = {}
        
        # Get vehicles details for items
        items_details = []
        for item in order.items:
            vehicle = await db.vehicles.find_one({"id": item.vehicle_id})
            if vehicle:
                items_details.append({
                    **item.dict(),
                    'vehicle_brand': vehicle.get('brand', ''),
                    'vehicle_model': vehicle.get('model', ''),
                    'license_plate': vehicle.get('license_plate', '')
                })
        
        # Generate accounting entries
        entries = accounting_system.generate_invoice_entries(
            invoice_data=invoice.dict(),
            client_data=client,
            items_data=items_details,
            settings=settings
        )
        
        # Save accounting entries to database
        for entry in entries:
            entry_dict = prepare_for_mongo(entry.dict())
            await db.accounting_entries.insert_one(entry_dict)
            
    except Exception as e:
        print(f"Erreur génération écritures comptables: {e}")
        # Continue even if accounting fails

@api_router.get("/orders", response_model=List[Order])
async def get_orders(current_user: User = Depends(get_current_user)):
    orders = await db.orders.find().to_list(1000)
    return [Order(**parse_from_mongo(order)) for order in orders]

@api_router.put("/orders/{order_id}", response_model=Order)
async def update_order(order_id: str, order_data: OrderCreate, current_user: User = Depends(get_current_user)):
    existing_order = await db.orders.find_one({"id": order_id})
    if not existing_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get client to calculate VAT
    client = await db.clients.find_one({"id": order_data.client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Process each item and calculate totals
    processed_items = []
    total_ht = 0
    
    for item in order_data.items:
        # Calculate number of days for this item
        days = calculate_days_between(item.start_date, item.end_date)
        
        # Calculate item total
        item_total_ht = item.daily_rate * item.quantity * days
        
        # Create processed item
        processed_item = OrderItem(
            vehicle_id=item.vehicle_id,
            quantity=item.quantity,
            daily_rate=item.daily_rate,
            total_days=days,
            is_renewable=item.is_renewable,
            rental_period=item.rental_period,
            rental_duration=item.rental_duration,
            start_date=item.start_date,
            end_date=item.end_date,
            item_total_ht=item_total_ht
        )
        
        processed_items.append(processed_item)
        total_ht += item_total_ht
    
    # Calculate VAT and totals
    vat_rate = client['vat_rate'] / 100
    total_vat = total_ht * vat_rate
    total_ttc = total_ht + total_vat
    
    # Calculate deposit VAT and grand total
    deposit_vat = order_data.deposit_amount * vat_rate if order_data.deposit_amount > 0 else 0
    grand_total = total_ttc + order_data.deposit_amount + deposit_vat
    
    updated_order = Order(
        id=order_id,
        client_id=order_data.client_id,
        order_number=existing_order['order_number'],
        items=processed_items,
        deposit_amount=order_data.deposit_amount,
        total_ht=total_ht,
        total_vat=total_vat,
        total_ttc=total_ttc,
        deposit_vat=deposit_vat,
        grand_total=grand_total,
        status=existing_order['status'],
        created_at=datetime.fromisoformat(existing_order['created_at']),
        created_by=existing_order['created_by']
    )
    
    order_dict = prepare_for_mongo(updated_order.dict())
    await db.orders.replace_one({"id": order_id}, order_dict)
    
    return updated_order

class OrderRenewalUpdate(BaseModel):
    is_renewable: bool
    rental_period: Optional[str] = None
    rental_duration: Optional[int] = None

@api_router.patch("/orders/{order_id}/renewal", response_model=dict)
async def update_order_renewal_settings(
    order_id: str, 
    renewal_data: OrderRenewalUpdate, 
    current_user: User = Depends(get_current_user)
):
    """Modifier les paramètres de reconductibilité d'une commande"""
    existing_order = await db.orders.find_one({"id": order_id})
    if not existing_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Mettre à jour tous les items de la commande
    update_fields = {}
    
    # Mise à jour de chaque item
    items = existing_order.get('items', [])
    for i, item in enumerate(items):
        update_fields[f"items.{i}.is_renewable"] = renewal_data.is_renewable
        if renewal_data.is_renewable:
            if renewal_data.rental_period:
                update_fields[f"items.{i}.rental_period"] = renewal_data.rental_period
            if renewal_data.rental_duration:
                update_fields[f"items.{i}.rental_duration"] = renewal_data.rental_duration
        else:
            # Si on désactive la reconductibilité, on retire les paramètres
            update_fields[f"items.{i}.rental_period"] = None
            update_fields[f"items.{i}.rental_duration"] = None
    
    # Exécuter la mise à jour
    await db.orders.update_one(
        {"id": order_id}, 
        {"$set": update_fields}
    )
    
    status_message = "activée" if renewal_data.is_renewable else "désactivée"
    return {
        "message": f"Reconductibilité {status_message} avec succès",
        "order_id": order_id,
        "is_renewable": renewal_data.is_renewable
    }

# Invoice endpoints
@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices(current_user: User = Depends(get_current_user)):
    invoices = await db.invoices.find().to_list(1000)
    return [Invoice(**parse_from_mongo(invoice)) for invoice in invoices]

@api_router.get("/invoices/overdue", response_model=List[Invoice])
async def get_overdue_invoices(current_user: User = Depends(get_current_user)):
    today = datetime.now(timezone.utc)
    invoices = await db.invoices.find({
        "due_date": {"$lt": today.isoformat()},
        "status": {"$in": ["sent", "overdue"]}
    }).to_list(1000)
    return [Invoice(**parse_from_mongo(invoice)) for invoice in invoices]

@api_router.put("/invoices/{invoice_id}/mark-paid")
async def mark_invoice_paid_legacy(invoice_id: str, current_user: User = Depends(get_current_user)):
    # Get invoice
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get client
    client = await db.clients.find_one({"id": invoice['client_id']})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Mark as paid
    payment_date = datetime.now(timezone.utc)
    result = await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {"status": "paid", "payment_date": payment_date.isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Generate accounting entries for payment
    try:
        settings = await db.settings.find_one()
        if not settings:
            settings = {}
            
        payment_entries = accounting_system.generate_payment_entries(
            invoice_data=invoice,
            client_data=client,
            payment_date=payment_date,
            payment_method="bank"
        )
        
        # Save accounting entries to database
        for entry in payment_entries:
            entry_dict = prepare_for_mongo(entry.dict())
            await db.accounting_entries.insert_one(entry_dict)
        
    except Exception as e:
        print(f"Erreur génération écritures de règlement: {e}")
    
    return {"message": "Invoice marked as paid and accounting entries generated"}

class PaymentCreate(BaseModel):
    amount: float
    payment_date: datetime
    payment_method: str
    reference: Optional[str] = None
    notes: Optional[str] = None

@api_router.post("/invoices/{invoice_id}/payments", response_model=Payment)
async def add_payment(
    invoice_id: str,
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user)
):
    # Get invoice
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Validate payment amount
    current_paid = invoice.get('amount_paid', 0)
    total_amount = invoice.get('grand_total', invoice.get('total_ttc', 0))
    
    if payment_data.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive")
    
    if current_paid + payment_data.amount > total_amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Payment amount exceeds remaining balance. Remaining: {total_amount - current_paid:.2f}€"
        )
    
    # Create payment record
    payment = Payment(
        invoice_id=invoice_id,
        amount=payment_data.amount,
        payment_date=payment_data.payment_date,
        payment_method=payment_data.payment_method,
        reference=payment_data.reference,
        notes=payment_data.notes,
        created_by=current_user.id
    )
    
    payment_dict = prepare_for_mongo(payment.dict())
    await db.payments.insert_one(payment_dict)
    
    # Update invoice
    new_amount_paid = current_paid + payment_data.amount
    new_remaining = total_amount - new_amount_paid
    
    update_data = {
        "amount_paid": new_amount_paid,
        "remaining_amount": new_remaining,
        "payment_date": payment_data.payment_date.isoformat()
    }
    
    # Update status based on remaining amount
    if new_remaining <= 0:
        update_data["status"] = "paid"
    elif new_amount_paid > 0:
        update_data["status"] = "partially_paid"
    
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": update_data}
    )
    
    return payment

@api_router.get("/invoices/{invoice_id}/payments", response_model=List[Payment])
async def get_invoice_payments(
    invoice_id: str, 
    current_user: User = Depends(get_current_user)
):
    payments = await db.payments.find({"invoice_id": invoice_id}).to_list(length=None)
    return [Payment(**payment) for payment in payments]

@api_router.delete("/payments/{payment_id}")
async def delete_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user)
):
    # Get payment
    payment = await db.payments.find_one({"id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Get invoice
    invoice = await db.invoices.find_one({"id": payment["invoice_id"]})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Update invoice amounts
    current_paid = invoice.get('amount_paid', 0)
    total_amount = invoice.get('grand_total', invoice.get('total_ttc', 0))
    
    new_amount_paid = max(0, current_paid - payment["amount"])
    new_remaining = total_amount - new_amount_paid
    
    update_data = {
        "amount_paid": new_amount_paid,
        "remaining_amount": new_remaining
    }
    
    # Update status
    if new_remaining >= total_amount:
        update_data["status"] = "draft"
        update_data["payment_date"] = None
    elif new_amount_paid > 0:
        update_data["status"] = "partially_paid"
    else:
        update_data["status"] = "sent"
    
    # Delete payment and update invoice
    await db.payments.delete_one({"id": payment_id})
    await db.invoices.update_one(
        {"id": payment["invoice_id"]},
        {"$set": update_data}
    )
    
    return {"message": "Payment deleted successfully"}

@api_router.put("/invoices/{invoice_id}/payment")
async def mark_invoice_paid(
    invoice_id: str,
    payment_date: datetime,
    current_user: User = Depends(get_current_user)
):
    """Legacy endpoint - marks invoice as fully paid with single payment"""
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    total_amount = invoice.get('grand_total', invoice.get('total_ttc', 0))
    current_paid = invoice.get('amount_paid', 0)
    remaining = total_amount - current_paid
    
    if remaining > 0:
        # Create payment for remaining amount
        payment_data = PaymentCreate(
            amount=remaining,
            payment_date=payment_date,
            payment_method="bank",
            notes="Full payment (legacy endpoint)"
        )
        await add_payment(invoice_id, payment_data, current_user)
    
    return {"message": "Invoice marked as paid"}

# PDF Generation endpoints
@api_router.post("/invoices/{invoice_id}/generate-pdf")
async def generate_invoice_pdf(invoice_id: str, current_user: User = Depends(get_current_user)):
    # Get invoice
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get client
    client = await db.clients.find_one({"id": invoice['client_id']})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get company settings
    settings = await db.settings.find_one()
    if not settings:
        settings = {}
    
    # Get vehicles details for items
    items_details = []
    for item in invoice['items']:
        vehicle = await db.vehicles.find_one({"id": item['vehicle_id']})
        if vehicle:
            item_detail = {
                **item,
                'vehicle_brand': vehicle.get('brand', ''),
                'vehicle_model': vehicle.get('model', ''),
                'license_plate': vehicle.get('license_plate', '')
            }
            items_details.append(item_detail)
    
    try:
        # Generate PDF
        pdf_data = await pdf_generator.generate_invoice_pdf(
            invoice_data=invoice,
            client_data=client,
            company_settings=settings,
            items_details=items_details
        )
        
        # Save PDF to invoice
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {"pdf_data": pdf_data, "status": "sent"}}
        )
        
        return {
            "message": "PDF generated successfully",
            "pdf_data": pdf_data
        }
        
    except Exception as e:
        print(f"Erreur génération PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

@api_router.get("/invoices/{invoice_id}/download-pdf")
async def download_invoice_pdf(invoice_id: str, current_user: User = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if not invoice.get('pdf_data'):
        raise HTTPException(status_code=404, detail="PDF not generated yet")
    
    pdf_bytes = base64.b64decode(invoice['pdf_data'])
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=facture_{invoice['invoice_number']}.pdf"
        }
    )

# Accounting endpoints
@api_router.get("/accounting/entries")
async def get_accounting_entries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    query = {}
    if start_date and end_date:
        query["entry_date"] = {
            "$gte": start_date,
            "$lte": end_date
        }
    
    entries = await db.accounting_entries.find(query).to_list(1000)
    return [AccountingEntry(**parse_from_mongo(entry)) for entry in entries]

@api_router.get("/accounting/summary")
async def get_accounting_summary(
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user)
):
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Get entries from database
        entries = await db.accounting_entries.find({
            "entry_date": {
                "$gte": start_dt.isoformat(),
                "$lte": end_dt.isoformat()
            }
        }).to_list(1000)
        
        # Convert to AccountingEntry objects
        accounting_entries = [AccountingEntry(**parse_from_mongo(entry)) for entry in entries]
        
        # Set entries in accounting system
        accounting_system.entries = accounting_entries
        
        # Generate summary
        summary = accounting_system.get_journal_entries_summary(start_dt, end_dt)
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error generating accounting summary: {str(e)}")

@api_router.get("/accounting/export/csv")
async def export_accounting_csv(
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user)
):
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Get entries from database
        entries = await db.accounting_entries.find({
            "entry_date": {
                "$gte": start_dt.isoformat(),
                "$lte": end_dt.isoformat()
            }
        }).to_list(1000)
        
        # Convert to AccountingEntry objects
        accounting_entries = [AccountingEntry(**parse_from_mongo(entry)) for entry in entries]
        
        # Generate CSV
        csv_data = accounting_system.export_to_csv(accounting_entries)
        
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=comptabilite_{start_date}_{end_date}.csv"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error exporting CSV: {str(e)}")

@api_router.get("/accounting/export/{format}")
async def export_accounting_format(
    format: str,
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user)
):
    if format not in ['ciel', 'sage', 'cegid']:
        raise HTTPException(status_code=400, detail="Format not supported. Use: ciel, sage, or cegid")
    
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Get entries from database
        entries = await db.accounting_entries.find({
            "entry_date": {
                "$gte": start_dt.isoformat(),
                "$lte": end_dt.isoformat()
            }
        }).to_list(1000)
        
        # Convert to AccountingEntry objects
        accounting_entries = [AccountingEntry(**parse_from_mongo(entry)) for entry in entries]
        
        # Generate export based on format
        if format == 'ciel':
            export_data = accounting_system.export_to_ciel(accounting_entries)
            filename = f"comptabilite_ciel_{start_date}_{end_date}.txt"
        elif format == 'sage':
            export_data = accounting_system.export_to_sage(accounting_entries)
            filename = f"comptabilite_sage_{start_date}_{end_date}.csv"
        elif format == 'cegid':
            export_data = accounting_system.export_to_cegid(accounting_entries)
            filename = f"comptabilite_cegid_{start_date}_{end_date}.csv"
        
        return Response(
            content=export_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error exporting {format}: {str(e)}")

# Dashboard endpoint
@api_router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user)):
    # Get counts
    clients_count = await db.clients.count_documents({})
    vehicles_count = await db.vehicles.count_documents({})
    orders_count = await db.orders.count_documents({})
    invoices_count = await db.invoices.count_documents({})
    
    # Get current month and year dates
    today = datetime.now(timezone.utc)
    current_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_year_start = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate monthly revenue (current month)
    monthly_invoices = await db.invoices.find({
        "status": "paid",
        "invoice_date": {
            "$gte": current_month_start.isoformat(),
            "$lt": today.isoformat()
        }
    }).to_list(length=None)
    
    monthly_revenue = sum(invoice.get('grand_total', invoice.get('total_ttc', 0)) for invoice in monthly_invoices)
    
    # Calculate yearly revenue (current year)
    yearly_invoices = await db.invoices.find({
        "status": "paid", 
        "invoice_date": {
            "$gte": current_year_start.isoformat(),
            "$lt": today.isoformat()
        }
    }).to_list(length=None)
    
    yearly_revenue = sum(invoice.get('grand_total', invoice.get('total_ttc', 0)) for invoice in yearly_invoices)
    
    # Get recent orders
    recent_orders = await db.orders.find().sort("created_at", -1).limit(5).to_list(length=None)
    
    # Get overdue invoices
    overdue_invoices = await db.invoices.find({
        "status": {"$ne": "paid"},
        "due_date": {"$lt": today.isoformat()}
    }).to_list(length=None)
    
    return {
        "stats": {
            "clients": clients_count,
            "vehicles": vehicles_count,
            "orders": orders_count,
            "invoices": invoices_count,
            "overdue_invoices": len(overdue_invoices),
            "monthly_revenue": monthly_revenue,
            "yearly_revenue": yearly_revenue
        },
        "recent_orders": [Order(**parse_from_mongo(order)) for order in recent_orders],
        "overdue_invoices": [Invoice(**parse_from_mongo(invoice)) for invoice in overdue_invoices]
    }

# Document management models
class VehicleDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: str
    label: str
    filename: str
    original_filename: str
    document_type: str  # registration_card, insurance, technical_control, other
    file_path: str
    file_size: int
    mime_type: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClientDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    label: str
    filename: str
    original_filename: str
    document_type: str  # driving_license, identity, business_registration, bank_details, other
    file_path: str
    file_size: int
    mime_type: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Settings endpoints
@api_router.get("/settings", response_model=Settings)
async def get_settings(current_user: User = Depends(get_current_user)):
    settings = await db.settings.find_one()
    if not settings:
        # Create default settings
        default_settings = Settings()
        settings_dict = prepare_for_mongo(default_settings.dict())
        await db.settings.insert_one(settings_dict)
        return default_settings
    return Settings(**settings)

@api_router.put("/settings", response_model=Settings)
async def update_settings(settings_data: Settings, current_user: User = Depends(get_current_user)):
    settings_dict = prepare_for_mongo(settings_data.dict())
    await db.settings.replace_one({}, settings_dict, upsert=True)
    return settings_data

# INSEE/Business validation endpoints
class BusinessValidationRequest(BaseModel):
    identifier: str
    
class BusinessValidationResponse(BaseModel):
    is_valid: bool
    identifier: str
    identifier_type: str
    company_info: Optional[CompanyInfo] = None
    validation_errors: List[str] = []

@api_router.post("/validate/business", response_model=BusinessValidationResponse)
async def validate_business(
    request: BusinessValidationRequest,
    current_user: User = Depends(get_current_user)
):
    """Validate French business using INSEE API"""
    try:
        identifier = request.identifier.strip()
        
        # Remove any spaces or formatting
        clean_identifier = ''.join(filter(str.isdigit, identifier))
        
        if len(clean_identifier) == 9:
            # SIREN validation
            is_valid = await insee_service.validate_siren(clean_identifier)
            identifier_type = "SIREN"
        elif len(clean_identifier) == 14:
            # SIRET validation
            is_valid = await insee_service.validate_siret(clean_identifier)
            identifier_type = "SIRET"
        else:
            return BusinessValidationResponse(
                is_valid=False,
                identifier=identifier,
                identifier_type="UNKNOWN",
                validation_errors=["Format invalide - doit être 9 chiffres (SIREN) ou 14 chiffres (SIRET)"]
            )
        
        company_info = None
        if is_valid:
            company_info = await insee_service.get_company_info(clean_identifier)
        
        return BusinessValidationResponse(
            is_valid=is_valid,
            identifier=clean_identifier,
            identifier_type=identifier_type,
            company_info=company_info,
            validation_errors=[] if is_valid else ["Entreprise non trouvée dans la base INSEE"]
        )
        
    except Exception as e:
        print(f"Erreur validation entreprise: {e}")
        return BusinessValidationResponse(
            is_valid=False,
            identifier=request.identifier,
            identifier_type="UNKNOWN",
            validation_errors=[f"Erreur lors de la validation: {str(e)}"]
        )

class AutoFillRequest(BaseModel):
    identifier: str

class AutoFillResponse(BaseModel):
    success: bool
    company_data: Dict[str, Any] = {}
    missing_fields: List[str] = []

@api_router.post("/autofill/business", response_model=AutoFillResponse)
async def autofill_business_data(
    request: AutoFillRequest,
    current_user: User = Depends(get_current_user)
):
    """Auto-fill business data from INSEE"""
    try:
        identifier = ''.join(filter(str.isdigit, request.identifier.strip()))
        
        if len(identifier) not in [9, 14]:
            return AutoFillResponse(
                success=False,
                missing_fields=["Format invalide"]
            )
        
        company_info = await insee_service.get_company_info(identifier)
        
        if not company_info:
            return AutoFillResponse(
                success=False,
                missing_fields=["Entreprise non trouvée"]
            )
        
        # Map company info to client form fields
        company_data = {}
        missing_fields = []
        
        if company_info.denomination:
            company_data['company_name'] = company_info.denomination
        else:
            missing_fields.append('company_name')
        
        if company_info.address:
            company_data['address'] = company_info.address
        else:
            missing_fields.append('address')
        
        if company_info.postal_code:
            company_data['postal_code'] = company_info.postal_code
        else:
            missing_fields.append('postal_code')
        
        if company_info.city:
            company_data['city'] = company_info.city
        else:
            missing_fields.append('city')
        
        if company_info.vat_number:
            company_data['vat_number'] = company_info.vat_number
        
        if company_info.siren:
            company_data['rcs_number'] = f"RCS {company_info.siren}"
        
        return AutoFillResponse(
            success=True,
            company_data=company_data,
            missing_fields=missing_fields
        )
        
    except Exception as e:
        print(f"Erreur auto-fill: {e}")
        return AutoFillResponse(
            success=False,
            missing_fields=[f"Erreur: {str(e)}"]
        )

# Email notification endpoints
class EmailNotificationRequest(BaseModel):
    recipient: EmailStr
    invoice_id: str

@api_router.post("/notifications/invoice")
async def send_invoice_notification(
    request: EmailNotificationRequest,
    current_user: User = Depends(get_current_user)
):
    """Send invoice notification email"""
    try:
        # Get invoice data
        invoice = await db.invoices.find_one({"id": request.invoice_id})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Get client data
        client = await db.clients.find_one({"id": invoice['client_id']})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Prepare invoice data for email
        invoice_data = {
            'invoice_number': invoice['invoice_number'],
            'client_name': client['company_name'],
            'invoice_date': invoice['invoice_date'],
            'total_ttc': invoice['total_ttc'],
            'due_date': invoice['due_date']
        }
        
        # Send email
        result = await mailgun_service.send_invoice_email(request.recipient, invoice_data)
        
        return {
            'success': result['success'],
            'message': result.get('message', result.get('error', 'Email envoyé'))
        }
        
    except Exception as e:
        print(f"Erreur envoi email facture: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur envoi email: {str(e)}")

class PaymentReminderRequest(BaseModel):
    recipient: EmailStr
    invoice_id: str
    urgency_level: str = "standard"  # standard or urgent

@api_router.post("/notifications/payment-reminder")
async def send_payment_reminder(
    request: PaymentReminderRequest,
    current_user: User = Depends(get_current_user)
):
    """Send payment reminder email"""
    try:
        # Get invoice data
        invoice = await db.invoices.find_one({"id": request.invoice_id})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Get client data
        client = await db.clients.find_one({"id": invoice['client_id']})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Calculate days overdue
        from datetime import datetime
        due_date = datetime.fromisoformat(invoice['due_date'].replace('Z', '+00:00'))
        days_overdue = max(0, (datetime.now(timezone.utc) - due_date).days)
        
        # Prepare reminder data for email
        reminder_data = {
            'invoice_number': invoice['invoice_number'],
            'client_name': client['company_name'],
            'amount_due': invoice['total_ttc'],
            'due_date': invoice['due_date'],
            'days_overdue': days_overdue,
            'urgency_level': request.urgency_level
        }
        
        # Send email
        result = await mailgun_service.send_payment_reminder(request.recipient, reminder_data)
        
        return {
            'success': result['success'],
            'message': result.get('message', result.get('error', 'Rappel envoyé'))
        }
        
    except Exception as e:
        print(f"Erreur envoi rappel paiement: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur envoi rappel: {str(e)}")

# Vehicle Document management endpoints
@api_router.get("/vehicles/{vehicle_id}/documents", response_model=List[VehicleDocument])
async def get_vehicle_documents(vehicle_id: str, current_user: User = Depends(get_current_user)):
    documents = await db.vehicle_documents.find({"vehicle_id": vehicle_id}).to_list(length=None)
    return [VehicleDocument(**parse_from_mongo(doc)) for doc in documents]

@api_router.post("/vehicles/{vehicle_id}/documents/upload")
async def upload_vehicle_document(
    vehicle_id: str,
    file: UploadFile = File(...),
    label: str = Form(...),
    document_type: str = Form(default="other"),
    current_user: User = Depends(get_current_user)
):
    # Vérifier que le véhicule existe
    vehicle = await db.vehicles.find_one({"id": vehicle_id})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Vérifier la taille du fichier (max 10MB)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Vérifier le type de fichier
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not supported")
    
    # Créer le répertoire de stockage
    import os
    upload_dir = f"/var/www/abetoile-location/uploads/vehicles/{vehicle_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Générer un nom de fichier unique
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    try:
        # Sauvegarder le fichier
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Créer l'enregistrement en base
        document = VehicleDocument(
            vehicle_id=vehicle_id,
            label=label,
            filename=unique_filename,
            original_filename=file.filename,
            document_type=document_type,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type
        )
        
        document_dict = prepare_for_mongo(document.dict())
        await db.vehicle_documents.insert_one(document_dict)
        
        return document
        
    except Exception as e:
        # Nettoyer le fichier en cas d'erreur
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@api_router.get("/vehicles/{vehicle_id}/documents/{document_id}/view")
async def view_vehicle_document(
    vehicle_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    document = await db.vehicle_documents.find_one({
        "id": document_id,
        "vehicle_id": vehicle_id
    })
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    import os
    if not os.path.exists(document["file_path"]):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    from fastapi.responses import FileResponse
    
    # Configuration spéciale pour la visualisation PDF
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    
    if document["mime_type"] == "application/pdf":
        # Pour les PDF, forcer l'affichage inline dans le navigateur
        headers["Content-Disposition"] = f'inline; filename="{document["original_filename"]}"'
        headers["Content-Type"] = "application/pdf"
        headers["X-Content-Type-Options"] = "nosniff"
        
        return FileResponse(
            path=document["file_path"],
            media_type="application/pdf",
            filename=document["original_filename"],
            headers=headers
        )
    else:
        # Pour les images, affichage normal
        return FileResponse(
            path=document["file_path"],
            media_type=document["mime_type"],
            filename=document["original_filename"],
            headers=headers
        )

@api_router.get("/vehicles/{vehicle_id}/documents/{document_id}/download")
async def download_vehicle_document(
    vehicle_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    document = await db.vehicle_documents.find_one({
        "id": document_id,
        "vehicle_id": vehicle_id
    })
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    import os
    if not os.path.exists(document["file_path"]):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=document["file_path"],
        media_type=document["mime_type"],
        filename=document["original_filename"],
        headers={"Content-Disposition": f"attachment; filename={document['original_filename']}"}
    )

@api_router.put("/vehicles/{vehicle_id}/documents/{document_id}")
async def update_vehicle_document(
    vehicle_id: str,
    document_id: str,
    update_data: dict,
    current_user: User = Depends(get_current_user)
):
    # Vérifier que le document existe
    document = await db.vehicle_documents.find_one({
        "id": document_id,
        "vehicle_id": vehicle_id
    })
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Mettre à jour seulement les champs autorisés
    allowed_fields = ["label", "document_type"]
    update_fields = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    if update_fields:
        await db.vehicle_documents.update_one(
            {"id": document_id, "vehicle_id": vehicle_id},
            {"$set": update_fields}
        )
    
    # Retourner le document mis à jour
    updated_document = await db.vehicle_documents.find_one({
        "id": document_id,
        "vehicle_id": vehicle_id
    })
    
    return VehicleDocument(**parse_from_mongo(updated_document))

@api_router.delete("/vehicles/{vehicle_id}/documents/{document_id}")
async def delete_vehicle_document(
    vehicle_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    # Récupérer le document
    document = await db.vehicle_documents.find_one({
        "id": document_id,
        "vehicle_id": vehicle_id
    })
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Supprimer le fichier du disque
    import os
    if os.path.exists(document["file_path"]):
        try:
            os.remove(document["file_path"])
        except OSError:
            pass  # Continuer même si la suppression échoue
    
    # Supprimer l'enregistrement de la base
    await db.vehicle_documents.delete_one({
        "id": document_id,
        "vehicle_id": vehicle_id
    })
    
    return {"message": "Document deleted successfully"}

# Client Document management endpoints
@api_router.get("/clients/{client_id}/documents", response_model=List[ClientDocument])
async def get_client_documents(client_id: str, current_user: User = Depends(get_current_user)):
    documents = await db.client_documents.find({"client_id": client_id}).to_list(length=None)
    return [ClientDocument(**parse_from_mongo(doc)) for doc in documents]

@api_router.post("/clients/{client_id}/documents/upload")
async def upload_client_document(
    client_id: str,
    file: UploadFile = File(...),
    label: str = Form(...),
    document_type: str = Form(default="other"),
    current_user: User = Depends(get_current_user)
):
    # Vérifier que le client existe
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Vérifier la taille du fichier (max 10MB)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Vérifier le type de fichier
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not supported")
    
    # Créer le répertoire de stockage
    import os
    upload_dir = f"/var/www/abetoile-location/uploads/clients/{client_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Générer un nom de fichier unique
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    try:
        # Sauvegarder le fichier
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Créer l'enregistrement en base
        document = ClientDocument(
            client_id=client_id,
            label=label,
            filename=unique_filename,
            original_filename=file.filename,
            document_type=document_type,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type
        )
        
        document_dict = prepare_for_mongo(document.dict())
        await db.client_documents.insert_one(document_dict)
        
        return document
        
    except Exception as e:
        # Nettoyer le fichier en cas d'erreur
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@api_router.get("/clients/{client_id}/documents/{document_id}/view")
async def view_client_document(
    client_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    document = await db.client_documents.find_one({
        "id": document_id,
        "client_id": client_id
    })
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    import os
    if not os.path.exists(document["file_path"]):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    from fastapi.responses import FileResponse
    
    # Configuration spéciale pour la visualisation PDF
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    
    if document["mime_type"] == "application/pdf":
        # Pour les PDF, forcer l'affichage inline dans le navigateur
        headers["Content-Disposition"] = f'inline; filename="{document["original_filename"]}"'
        headers["Content-Type"] = "application/pdf"
        headers["X-Content-Type-Options"] = "nosniff"
        
        return FileResponse(
            path=document["file_path"],
            media_type="application/pdf",
            filename=document["original_filename"],
            headers=headers
        )
    else:
        # Pour les images, affichage normal
        return FileResponse(
            path=document["file_path"],
            media_type=document["mime_type"],
            filename=document["original_filename"],
            headers=headers
        )

@api_router.get("/clients/{client_id}/documents/{document_id}/download")
async def download_client_document(
    client_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    document = await db.client_documents.find_one({
        "id": document_id,
        "client_id": client_id
    })
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    import os
    if not os.path.exists(document["file_path"]):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=document["file_path"],
        media_type=document["mime_type"],
        filename=document["original_filename"],
        headers={"Content-Disposition": f"attachment; filename={document['original_filename']}"}
    )

@api_router.put("/clients/{client_id}/documents/{document_id}")
async def update_client_document(
    client_id: str,
    document_id: str,
    update_data: dict,
    current_user: User = Depends(get_current_user)
):
    # Vérifier que le document existe
    document = await db.client_documents.find_one({
        "id": document_id,
        "client_id": client_id
    })
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Mettre à jour seulement les champs autorisés
    allowed_fields = ["label", "document_type"]
    update_fields = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    if update_fields:
        await db.client_documents.update_one(
            {"id": document_id, "client_id": client_id},
            {"$set": update_fields}
        )
    
    # Retourner le document mis à jour
    updated_document = await db.client_documents.find_one({
        "id": document_id,
        "client_id": client_id
    })
    
    return ClientDocument(**parse_from_mongo(updated_document))

@api_router.delete("/clients/{client_id}/documents/{document_id}")
async def delete_client_document(
    client_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    # Récupérer le document
    document = await db.client_documents.find_one({
        "id": document_id,
        "client_id": client_id
    })
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Supprimer le fichier du disque
    import os
    if os.path.exists(document["file_path"]):
        try:
            os.remove(document["file_path"])
        except OSError:
            pass  # Continuer même si la suppression échoue
    
    # Supprimer l'enregistrement de la base
    await db.client_documents.delete_one({
        "id": document_id,
        "client_id": client_id
    })
    
    return {"message": "Document deleted successfully"}

# Order renewal endpoint
@api_router.post("/orders/renew")
async def trigger_order_renewal(current_user: User = Depends(get_current_user)):
    """Manually trigger order renewal process"""
    try:
        await renew_orders()
        return {"message": "Order renewal process completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during renewal: {str(e)}")

# Maintenance endpoints
@api_router.post("/maintenance", response_model=MaintenanceRecord)
async def create_maintenance_record(
    maintenance_data: MaintenanceRecordCreate,
    current_user: User = Depends(get_current_user)
):
    """Créer un nouveau enregistrement de maintenance/réparation"""
    # Vérifier que le véhicule existe
    vehicle = await db.vehicles.find_one({"id": maintenance_data.vehicle_id})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Calculer automatiquement les montants
    vat_amount = maintenance_data.amount_ht * (maintenance_data.vat_rate / 100)
    amount_ttc = maintenance_data.amount_ht + vat_amount
    
    maintenance_record = MaintenanceRecord(
        vehicle_id=maintenance_data.vehicle_id,
        maintenance_type=maintenance_data.maintenance_type,
        description=maintenance_data.description,
        maintenance_date=maintenance_data.maintenance_date,
        amount_ht=maintenance_data.amount_ht,
        vat_rate=maintenance_data.vat_rate,
        vat_amount=vat_amount,
        amount_ttc=amount_ttc,
        supplier=maintenance_data.supplier,
        notes=maintenance_data.notes,
        created_by=current_user.id
    )
    
    maintenance_dict = prepare_for_mongo(maintenance_record.dict())
    await db.maintenance_records.insert_one(maintenance_dict)
    
    return maintenance_record

@api_router.get("/maintenance", response_model=List[MaintenanceRecord])
async def get_maintenance_records(
    vehicle_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Récupérer les enregistrements de maintenance"""
    query = {}
    if vehicle_id:
        query["vehicle_id"] = vehicle_id
    
    records = await db.maintenance_records.find(query).sort("maintenance_date", -1).to_list(length=None)
    return [MaintenanceRecord(**parse_from_mongo(record)) for record in records]

@api_router.get("/maintenance/{record_id}", response_model=MaintenanceRecord)
async def get_maintenance_record(
    record_id: str,
    current_user: User = Depends(get_current_user)
):
    """Récupérer un enregistrement de maintenance spécifique"""
    record = await db.maintenance_records.find_one({"id": record_id})
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    
    return MaintenanceRecord(**parse_from_mongo(record))

@api_router.put("/maintenance/{record_id}", response_model=MaintenanceRecord)
async def update_maintenance_record(
    record_id: str,
    maintenance_data: MaintenanceRecordCreate,
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un enregistrement de maintenance"""
    existing_record = await db.maintenance_records.find_one({"id": record_id})
    if not existing_record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    
    # Vérifier que le véhicule existe
    vehicle = await db.vehicles.find_one({"id": maintenance_data.vehicle_id})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Calculer automatiquement les montants
    vat_amount = maintenance_data.amount_ht * (maintenance_data.vat_rate / 100)
    amount_ttc = maintenance_data.amount_ht + vat_amount
    
    updated_record = MaintenanceRecord(
        id=record_id,
        vehicle_id=maintenance_data.vehicle_id,
        maintenance_type=maintenance_data.maintenance_type,
        description=maintenance_data.description,
        maintenance_date=maintenance_data.maintenance_date,
        amount_ht=maintenance_data.amount_ht,
        vat_rate=maintenance_data.vat_rate,
        vat_amount=vat_amount,
        amount_ttc=amount_ttc,
        supplier=maintenance_data.supplier,
        documents=existing_record.get('documents', []),  # Conserver les documents existants
        notes=maintenance_data.notes,
        created_at=datetime.fromisoformat(existing_record['created_at']),
        created_by=existing_record['created_by']
    )
    
    maintenance_dict = prepare_for_mongo(updated_record.dict())
    await db.maintenance_records.replace_one({"id": record_id}, maintenance_dict)
    
    return updated_record

@api_router.delete("/maintenance/{record_id}")
async def delete_maintenance_record(
    record_id: str,
    current_user: User = Depends(get_current_user)
):
    """Supprimer un enregistrement de maintenance"""
    record = await db.maintenance_records.find_one({"id": record_id})
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    
    # Supprimer les documents associés
    for doc_id in record.get('documents', []):
        await db.documents.delete_one({"id": doc_id})
        # Supprimer le fichier physique si nécessaire
        file_path = f"/app/documents/{doc_id}"
        try:
            os.remove(file_path)
        except OSError:
            pass
    
    await db.maintenance_records.delete_one({"id": record_id})
    
    return {"message": "Maintenance record deleted successfully"}

# Document management for maintenance records
@api_router.post("/maintenance/{record_id}/documents")
async def upload_maintenance_document(
    record_id: str,
    file: UploadFile = File(...),
    label: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Upload un document pour un enregistrement de maintenance"""
    # Vérifier que l'enregistrement existe
    record = await db.maintenance_records.find_one({"id": record_id})
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    
    # Vérifier le type de fichier
    allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="Type de fichier non autorisé. Seuls PDF, JPG et PNG sont acceptés."
        )
    
    # Vérifier la taille (max 10MB)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size too large (max 10MB)")
    
    # Créer le document
    document = Document(
        name=file.filename,
        filename=file.filename,
        content_type=file.content_type,
        size=len(content),
        label=label or file.filename,
        created_by=current_user.id
    )
    
    # Sauvegarder le fichier
    os.makedirs("/app/documents", exist_ok=True)
    file_path = f"/app/documents/{document.id}"
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Sauvegarder le document en base
    document_dict = prepare_for_mongo(document.dict())
    await db.documents.insert_one(document_dict)
    
    # Ajouter le document à l'enregistrement de maintenance
    await db.maintenance_records.update_one(
        {"id": record_id},
        {"$push": {"documents": document.id}}
    )
    
    return {"message": "Document uploaded successfully", "document_id": document.id}

@api_router.get("/maintenance/{record_id}/documents")
async def get_maintenance_documents(
    record_id: str,
    current_user: User = Depends(get_current_user)
):
    """Récupérer les documents d'un enregistrement de maintenance"""
    record = await db.maintenance_records.find_one({"id": record_id})
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    
    doc_ids = record.get('documents', [])
    if not doc_ids:
        return []
    
    documents = await db.documents.find({"id": {"$in": doc_ids}}).to_list(length=None)
    return [Document(**parse_from_mongo(doc)) for doc in documents]

@api_router.get("/documents/{document_id}/download")
async def download_maintenance_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Télécharger un document de maintenance"""
    document = await db.documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = f"/app/documents/{document_id}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=document['filename'],
        media_type=document['content_type']
    )

@api_router.delete("/documents/{document_id}")
async def delete_maintenance_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Supprimer un document de maintenance"""
    document = await db.documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Supprimer le fichier physique
    file_path = f"/app/documents/{document_id}"
    try:
        os.remove(file_path)
    except OSError:
        pass
    
    # Supprimer de la base de données
    await db.documents.delete_one({"id": document_id})
    
    # Retirer de tous les enregistrements de maintenance
    await db.maintenance_records.update_many(
        {"documents": document_id},
        {"$pull": {"documents": document_id}}
    )
    
    return {"message": "Document deleted successfully"}

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def renew_orders():
    """Renew eligible orders automatically with dynamic day calculation"""
    try:
        today = datetime.now(timezone.utc)
        
        # Find orders that need renewal
        renewable_orders = await db.orders.find({
            "status": "active",
            "items.is_renewable": True
        }).to_list(length=None)
        
        for order_data in renewable_orders:
            order = Order(**order_data)
            
            for item in order.items:
                if item.is_renewable and item.rental_period and item.rental_duration:
                    # Calculate next renewal date based on end_date + renewal period
                    current_end_date = item.end_date
                    
                    # Calculate new period dates
                    if item.rental_period == RentalPeriod.DAYS:
                        new_start_date = current_end_date + timedelta(days=1)
                        new_end_date = new_start_date + timedelta(days=item.rental_duration - 1)
                    elif item.rental_period == RentalPeriod.WEEKS:
                        new_start_date = current_end_date + timedelta(days=1)
                        new_end_date = new_start_date + timedelta(weeks=item.rental_duration) - timedelta(days=1)
                    elif item.rental_period == RentalPeriod.MONTHS:
                        new_start_date = current_end_date + timedelta(days=1)
                        # For monthly, calculate the actual days in the next period
                        if item.rental_duration == 1:
                            # Next month
                            if new_start_date.month == 12:
                                next_month = new_start_date.replace(year=new_start_date.year + 1, month=1)
                            else:
                                next_month = new_start_date.replace(month=new_start_date.month + 1)
                            
                            # Calculate days in the month
                            if next_month.month == 12:
                                days_in_month = (next_month.replace(year=next_month.year + 1, month=1) - next_month).days
                            else:
                                days_in_month = (next_month.replace(month=next_month.month + 1) - next_month).days
                            
                            new_end_date = new_start_date + timedelta(days=days_in_month - 1)
                        else:
                            # Multiple months - approximate with 30 days per month
                            new_end_date = new_start_date + timedelta(days=item.rental_duration * 30 - 1)
                    elif item.rental_period == RentalPeriod.YEARS:
                        new_start_date = current_end_date + timedelta(days=1)
                        new_end_date = new_start_date + timedelta(days=item.rental_duration * 365 - 1)
                    else:
                        continue
                    
                    # Check if it's time to renew (renewal date has passed)
                    if new_start_date.date() <= today.date():
                        # Check if last invoice was paid
                        last_invoice = await db.invoices.find_one(
                            {"order_id": order.id},
                            sort=[("created_at", -1)]
                        )
                        
                        if last_invoice and last_invoice.get('status') == 'paid':
                            # Create new order item with updated dates and recalculated amount
                            days = calculate_days_between(new_start_date, new_end_date)
                            item_total_ht = item.daily_rate * item.quantity * days
                            
                            renewed_item = OrderItem(
                                vehicle_id=item.vehicle_id,
                                quantity=item.quantity,
                                daily_rate=item.daily_rate,
                                total_days=days,
                                is_renewable=item.is_renewable,
                                rental_period=item.rental_period,
                                rental_duration=item.rental_duration,
                                start_date=new_start_date,
                                end_date=new_end_date,
                                item_total_ht=item_total_ht
                            )
                            
                            # Update order with new item dates and totals
                            client = await db.clients.find_one({"id": order.client_id})
                            if client:
                                vat_rate = client['vat_rate'] / 100
                                
                                # Create renewal order
                                renewal_order = Order(
                                    client_id=order.client_id,
                                    order_number=f"{order.order_number}-R{int(today.timestamp())}",
                                    items=[renewed_item],
                                    deposit_amount=0,  # No deposit on renewals
                                    total_ht=item_total_ht,
                                    total_vat=item_total_ht * vat_rate,
                                    total_ttc=item_total_ht * (1 + vat_rate),
                                    deposit_vat=0,
                                    grand_total=item_total_ht * (1 + vat_rate),
                                    created_by="system"
                                )
                                
                                # Save renewal order
                                renewal_dict = prepare_for_mongo(renewal_order.dict())
                                await db.orders.insert_one(renewal_dict)
                                
                                # Create invoice for renewal
                                await create_invoice_from_order(renewal_order, client)
                                
                                # Update original order item end dates
                                await db.orders.update_one(
                                    {"id": order.id, "items.vehicle_id": item.vehicle_id},
                                    {"$set": {"items.$.end_date": new_end_date.isoformat()}}
                                )
                                
                                print(f"Order {order.order_number} renewed successfully with {days} days")
                    
    except Exception as e:
        print(f"Error in order renewal: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()