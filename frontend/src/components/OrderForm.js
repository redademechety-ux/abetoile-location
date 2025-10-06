import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Save, ArrowLeft, Plus, Trash2, Calendar } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const OrderForm = () => {
  const navigate = useNavigate();

  const [clients, setClients] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [formData, setFormData] = useState({
    client_id: '',
    items: [{
      vehicle_id: '',
      quantity: 1,
      daily_rate: 0,
      is_renewable: false,
      rental_period: '',
      rental_duration: 1,
      start_date: new Date().toISOString().split('T')[0],
      end_date: new Date().toISOString().split('T')[0]
    }],
    deposit_amount: 0
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [clientsRes, vehiclesRes] = await Promise.all([
        axios.get(`${API}/clients`),
        axios.get(`${API}/vehicles`)
      ]);
      
      setClients(clientsRes.data);
      setVehicles(vehiclesRes.data.filter(v => v.is_available));
    } catch (error) {
      setError('Erreur lors du chargement des données');
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  const addItem = () => {
    setFormData(prev => ({
      ...prev,
      items: [...prev.items, {
        vehicle_id: '',
        quantity: 1,
        daily_rate: 0,
        is_renewable: false,
        rental_period: '',
        rental_duration: 1,
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0]
      }]
    }));
  };

  const removeItem = (index) => {
    setFormData(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }));
  };

  // Fonction pour calculer le nombre de jours
  const calculateDays = (startDate, endDate) => {
    if (!startDate || !endDate) return 1;
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1; // Include both dates
    return Math.max(1, diffDays);
  };

  // Fonction pour calculer le total d'un item
  const calculateItemTotal = (item) => {
    const days = calculateDays(item.start_date, item.end_date);
    return (item.daily_rate * item.quantity * days) || 0;
  };

  // Fonction pour calculer le total de la commande
  const calculateOrderTotal = () => {
    const itemsTotal = formData.items.reduce((sum, item) => sum + calculateItemTotal(item), 0);
    return itemsTotal + (formData.deposit_amount || 0);
  };

  const updateItem = (index, field, value) => {
    setFormData(prev => {
      const newItems = [...prev.items];
      newItems[index] = { ...newItems[index], [field]: value };
      
      // Auto-fill daily rate when vehicle is selected
      if (field === 'vehicle_id') {
        const vehicle = vehicles.find(v => v.id === value);
        if (vehicle) {
          newItems[index].daily_rate = vehicle.daily_rate;
        }
      }
      
      return { ...prev, items: newItems };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    if (formData.items.length === 0) {
      setError('Veuillez ajouter au moins un véhicule à la commande');
      setSaving(false);
      return;
    }

    try {
      await axios.post(`${API}/orders`, formData);
      setSuccess('Commande créée avec succès');
      
      setTimeout(() => {
        navigate('/orders');
      }, 1500);
    } catch (error) {
      setError(error.response?.data?.detail || 'Erreur lors de la création de la commande');
    } finally {
      setSaving(false);
    }
  };

  const getVehicleName = (vehicleId) => {
    const vehicle = vehicles.find(v => v.id === vehicleId);
    return vehicle ? `${vehicle.brand} ${vehicle.model} (${vehicle.license_plate})` : '';
  };

  const calculateTotal = () => {
    return formData.items.reduce((total, item) => {
      return total + (item.daily_rate * item.quantity);
    }, 0);
  };

  const getSelectedClient = () => {
    return clients.find(c => c.id === formData.client_id);
  };

  const calculateTotalWithVAT = () => {
    const total = calculateTotal();
    const client = getSelectedClient();
    const vatRate = client ? client.vat_rate : 20;
    const vat = total * (vatRate / 100);
    return { total, vat, totalWithVat: total + vat };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const totals = calculateTotalWithVAT();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/orders')}
          className="btn btn-secondary"
        >
          <ArrowLeft size={20} />
          Retour
        </button>
        <h1 className="text-3xl font-bold text-gray-900">Nouvelle commande</h1>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Informations générales</h2>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="form-group">
                <label className="form-label">Client *</label>
                <select
                  value={formData.client_id}
                  onChange={(e) => setFormData(prev => ({ ...prev, client_id: e.target.value }))}
                  className="form-select"
                  required
                >
                  <option value="">Sélectionner un client</option>
                  {clients.map(client => (
                    <option key={client.id} value={client.id}>
                      {client.company_name} - {client.contact_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Date de début *</label>
                <input
                  type="datetime-local"
                  value={formData.start_date}
                  onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
                  className="form-input"
                  required
                />
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="flex items-center justify-between">
              <h2 className="card-title">Véhicules</h2>
              <button
                type="button"
                onClick={addItem}
                className="btn btn-primary btn-sm"
              >
                <Plus size={16} />
                Ajouter un véhicule
              </button>
            </div>
          </div>
          <div className="card-content">
            {formData.items.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 mb-4">Aucun véhicule ajouté</p>
                <button
                  type="button"
                  onClick={addItem}
                  className="btn btn-primary"
                >
                  <Plus size={20} />
                  Ajouter le premier véhicule
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {formData.items.map((item, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      <div className="form-group">
                        <label className="form-label">Véhicule *</label>
                        <select
                          value={item.vehicle_id}
                          onChange={(e) => updateItem(index, 'vehicle_id', e.target.value)}
                          className="form-select"
                          required
                        >
                          <option value="">Sélectionner un véhicule</option>
                          {vehicles.map(vehicle => (
                            <option key={vehicle.id} value={vehicle.id}>
                              {vehicle.brand} {vehicle.model} - {vehicle.license_plate}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="form-group">
                        <label className="form-label">Quantité</label>
                        <input
                          type="number"
                          min="1"
                          value={item.quantity}
                          onChange={(e) => updateItem(index, 'quantity', parseInt(e.target.value) || 1)}
                          className="form-input"
                        />
                      </div>

                      <div className="form-group">
                        <label className="form-label">Tarif/jour (€)</label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          value={item.daily_rate}
                          onChange={(e) => updateItem(index, 'daily_rate', parseFloat(e.target.value) || 0)}
                          className="form-input"
                        />
                      </div>

                      <div className="form-group">
                        <label className="form-label">Actions</label>
                        <button
                          type="button"
                          onClick={() => removeItem(index)}
                          className="btn btn-danger btn-sm"
                        >
                          <Trash2 size={16} />
                          Supprimer
                        </button>
                      </div>
                    </div>

                    <div className="mt-4 border-t pt-4">
                      <div className="flex items-center gap-4 mb-4">
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={item.is_renewable}
                            onChange={(e) => updateItem(index, 'is_renewable', e.target.checked)}
                            className="rounded"
                          />
                          Location reconductible
                        </label>
                      </div>

                      {item.is_renewable && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div className="form-group">
                            <label className="form-label">Période</label>
                            <select
                              value={item.rental_period}
                              onChange={(e) => updateItem(index, 'rental_period', e.target.value)}
                              className="form-select"
                            >
                              <option value="days">Jours</option>
                              <option value="weeks">Semaines</option>
                              <option value="months">Mois</option>
                              <option value="years">Années</option>
                            </select>
                          </div>

                          <div className="form-group">
                            <label className="form-label">Durée</label>
                            <input
                              type="number"
                              min="1"
                              value={item.rental_duration}
                              onChange={(e) => updateItem(index, 'rental_duration', parseInt(e.target.value) || 1)}
                              className="form-input"
                            />
                          </div>

                          <div className="form-group">
                            <label className="form-label">Date de fin (optionnel)</label>
                            <input
                              type="date"
                              value={item.end_date}
                              onChange={(e) => updateItem(index, 'end_date', e.target.value)}
                              className="form-input"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {formData.items.length > 0 && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Récapitulatif</h2>
            </div>
            <div className="card-content">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Total HT:</span>
                  <span className="font-medium">{totals.total.toFixed(2)} €</span>
                </div>
                <div className="flex justify-between">
                  <span>TVA ({getSelectedClient()?.vat_rate || 20}%):</span>
                  <span className="font-medium">{totals.vat.toFixed(2)} €</span>
                </div>
                <div className="flex justify-between text-lg font-bold border-t pt-2">
                  <span>Total TTC:</span>
                  <span>{totals.totalWithVat.toFixed(2)} €</span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="flex gap-4">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={saving || formData.items.length === 0}
          >
            {saving ? (
              <span className="loading-spinner"></span>
            ) : (
              <>
                <Save size={20} />
                Créer la commande
              </>
            )}
          </button>
          <button
            type="button"
            onClick={() => navigate('/orders')}
            className="btn btn-secondary"
          >
            Annuler
          </button>
        </div>
      </form>
    </div>
  );
};

export default OrderForm;