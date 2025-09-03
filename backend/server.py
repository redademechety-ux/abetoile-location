from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
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
app = FastAPI(title="AutoPro Rental Management", version="1.0.0")

# Create API router
api_router = APIRouter(prefix="/api")

# Enums
class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
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
    daily_rate: float
    is_renewable: bool = False
    rental_period: Optional[RentalPeriod] = None
    rental_duration: Optional[int] = None
    end_date: Optional[datetime] = None

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    order_number: str
    items: List[OrderItem]
    start_date: datetime
    total_ht: float
    total_vat: float
    total_ttc: float
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str

class OrderCreate(BaseModel):
    client_id: str
    items: List[OrderItem]
    start_date: datetime

class Invoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str
    order_id: str
    client_id: str
    invoice_date: datetime
    due_date: datetime
    items: List[OrderItem]
    total_ht: float
    total_vat: float
    total_ttc: float
    status: InvoiceStatus = InvoiceStatus.DRAFT
    payment_date: Optional[datetime] = None
    pdf_data: Optional[str] = None  # Base64 encoded PDF
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Settings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str = "AutoPro Rental"
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
@api_router.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate, current_user: User = Depends(get_current_user)):
    # Get client to calculate VAT
    client = await db.clients.find_one({"id": order_data.client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Calculate totals
    total_ht = sum(item.daily_rate * item.quantity for item in order_data.items)
    total_vat = total_ht * (client['vat_rate'] / 100)
    total_ttc = total_ht + total_vat
    
    order_number = await generate_order_number()
    
    order = Order(
        client_id=order_data.client_id,
        order_number=order_number,
        items=order_data.items,
        start_date=order_data.start_date,
        total_ht=total_ht,
        total_vat=total_vat,
        total_ttc=total_ttc,
        created_by=current_user.id
    )
    
    order_dict = prepare_for_mongo(order.dict())
    await db.orders.insert_one(order_dict)
    
    # Create initial invoice
    await create_invoice_from_order(order, client)
    
    return order

async def create_invoice_from_order(order: Order, client: dict):
    invoice_number = await generate_invoice_number()
    due_date = order.start_date + timedelta(days=30)  # Default 30 days
    
    invoice = Invoice(
        invoice_number=invoice_number,
        order_id=order.id,
        client_id=order.client_id,
        invoice_date=datetime.now(timezone.utc),
        due_date=due_date,
        items=order.items,
        total_ht=order.total_ht,
        total_vat=order.total_vat,
        total_ttc=order.total_ttc,
        status=InvoiceStatus.DRAFT
    )
    
    invoice_dict = prepare_for_mongo(invoice.dict())
    await db.invoices.insert_one(invoice_dict)

@api_router.get("/orders", response_model=List[Order])
async def get_orders(current_user: User = Depends(get_current_user)):
    orders = await db.orders.find().to_list(1000)
    return [Order(**parse_from_mongo(order)) for order in orders]

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
async def mark_invoice_paid(invoice_id: str, current_user: User = Depends(get_current_user)):
    result = await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {"status": "paid", "payment_date": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"message": "Invoice marked as paid"}

# Dashboard endpoint
@api_router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user)):
    today = datetime.now(timezone.utc)
    
    # Count overdue invoices
    overdue_count = await db.invoices.count_documents({
        "due_date": {"$lt": today.isoformat()},
        "status": {"$in": ["sent", "overdue"]}
    })
    
    # Count active orders
    active_orders = await db.orders.count_documents({"status": "active"})
    
    # Count clients
    total_clients = await db.clients.count_documents({"is_active": True})
    
    # Count vehicles
    total_vehicles = await db.vehicles.count_documents({})
    
    return {
        "overdue_invoices": overdue_count,
        "active_orders": active_orders,
        "total_clients": total_clients,
        "total_vehicles": total_vehicles
    }

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()