import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Save, ArrowLeft, Upload, Calendar } from 'lucide-react';
import VehicleDocuments from './VehicleDocuments';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VehicleForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = !!id;

  const [formData, setFormData] = useState({
    type: 'car',
    brand: '',
    model: '',
    license_plate: '',
    first_registration: '',
    technical_control_expiry: '',
    insurance_company: '',
    insurance_contract: '',
    insurance_amount: 0,
    insurance_expiry: '',
    daily_rate: 0,
    accounting_account: '706000'
  });

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeTab, setActiveTab] = useState('info');

  useEffect(() => {
    if (isEdit) {
      fetchVehicle();
    }
  }, [id, isEdit]);

  const fetchVehicle = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/vehicles/${id}`);
      const vehicle = response.data;
      
      // Format dates for input fields
      const formatDate = (dateString) => {
        if (!dateString) return '';
        return new Date(dateString).toISOString().split('T')[0];
      };

      setFormData({
        ...vehicle,
        first_registration: formatDate(vehicle.first_registration),
        technical_control_expiry: formatDate(vehicle.technical_control_expiry),
        insurance_expiry: formatDate(vehicle.insurance_expiry)
      });
    } catch (error) {
      setError('Erreur lors du chargement du véhicule');
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      // Convert date strings to ISO format
      const submitData = {
        ...formData,
        first_registration: new Date(formData.first_registration).toISOString(),
        technical_control_expiry: new Date(formData.technical_control_expiry).toISOString(),
        insurance_expiry: new Date(formData.insurance_expiry).toISOString()
      };

      if (isEdit) {
        await axios.put(`${API}/vehicles/${id}`, submitData);
        setSuccess('Véhicule modifié avec succès');
      } else {
        const response = await axios.post(`${API}/vehicles`, submitData);
        setSuccess('Véhicule créé avec succès');
        // Rediriger vers l'edition pour pouvoir ajouter des documents
        setTimeout(() => {
          navigate(`/vehicles/edit/${response.data.id}`, { replace: true });
          setActiveTab('documents');
        }, 1500);
        return;
      }
      
    } catch (error) {
      setError(error.response?.data?.detail || 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/vehicles')}
          className="btn btn-secondary"
        >
          <ArrowLeft size={20} />
          Retour
        </button>
        <h1 className="text-3xl font-bold text-gray-900">
          {isEdit ? 'Modifier le véhicule' : 'Nouveau véhicule'}
        </h1>
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

      {/* Onglets */}
      {isEdit && (
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('info')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'info'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Informations
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'documents'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Documents
            </button>
          </nav>
        </div>
      )}

      {/* Contenu des onglets */}
      {activeTab === 'info' && (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Informations du véhicule</h2>
            </div>
            <div className="card-content">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="form-group">
                  <label className="form-label">Type de véhicule *</label>
                  <select
                    name="type"
                    value={formData.type}
                    onChange={handleChange}
                    className="form-select"
                    required
                  >
                    <option value="car">Voiture</option>
                    <option value="van">Camionnette</option>
                    <option value="truck">Camion</option>
                    <option value="motorcycle">Moto</option>
                    <option value="other">Autre</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Immatriculation *</label>
                  <input
                    type="text"
                    name="license_plate"
                    value={formData.license_plate}
                    onChange={handleChange}
                    className="form-input font-mono"
                    placeholder="AB-123-CD"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Marque *</label>
                  <input
                    type="text"
                    name="brand"
                    value={formData.brand}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Modèle *</label>
                  <input
                    type="text"
                    name="model"
                    value={formData.model}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Date de première mise en circulation *</label>
                  <input
                    type="date"
                    name="first_registration"
                    value={formData.first_registration}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Date d'expiration du contrôle technique *</label>
                  <input
                    type="date"
                    name="technical_control_expiry"
                    value={formData.technical_control_expiry}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Tarif journalier (€) *</label>
                  <input
                    type="number"
                    step="0.01"
                    name="daily_rate"
                    value={formData.daily_rate}
                    onChange={handleChange}
                    className="form-input"
                    min="0"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Compte comptable</label>
                  <input
                    type="text"
                    name="accounting_account"
                    value={formData.accounting_account}
                    onChange={handleChange}
                    className="form-input"
                    placeholder="706000"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Informations d'assurance</h2>
            </div>
            <div className="card-content">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="form-group">
                  <label className="form-label">Compagnie d'assurance *</label>
                  <input
                    type="text"
                    name="insurance_company"
                    value={formData.insurance_company}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Numéro de contrat *</label>
                  <input
                    type="text"
                    name="insurance_contract"
                    value={formData.insurance_contract}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Montant de l'assurance (€) *</label>
                  <input
                    type="number"
                    step="0.01"
                    name="insurance_amount"
                    value={formData.insurance_amount}
                    onChange={handleChange}
                    className="form-input"
                    min="0"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Date d'expiration de l'assurance *</label>
                  <input
                    type="date"
                    name="insurance_expiry"
                    value={formData.insurance_expiry}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="flex gap-4">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={saving}
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Sauvegarde...
                </>
              ) : (
                <>
                  <Save size={20} />
                  {isEdit ? 'Modifier' : 'Créer'}
                </>
              )}
            </button>

            <button
              type="button"
              onClick={() => navigate('/vehicles')}
              className="btn btn-secondary"
            >
              Annuler
            </button>
          </div>
        </form>
      )}

      {/* Onglet Documents */}
      {activeTab === 'documents' && isEdit && (
        <div className="card">
          <div className="card-content">
            <VehicleDocuments 
              vehicleId={id} 
              onDocumentUpdate={() => {
                // Callback pour rafraîchir si nécessaire
              }} 
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default VehicleForm;