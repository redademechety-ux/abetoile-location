import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Save, ArrowLeft, Upload, User } from 'lucide-react';
import ClientDocuments from './ClientDocuments';
import BusinessValidation from './BusinessValidation';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ClientForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = !!id;

  const [formData, setFormData] = useState({
    company_name: '',
    contact_person: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    postal_code: '',
    country: 'France',
    vat_rate: 20.0,
    intra_vat_number: '',
    rcs_number: '',
    notes: ''
  });

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeTab, setActiveTab] = useState('info');
  const [businessValidationError, setBusinessValidationError] = useState('');

  useEffect(() => {
    if (isEdit) {
      fetchClient();
    }
  }, [id, isEdit]);

  const fetchClient = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/clients/${id}`);
      setFormData(response.data);
    } catch (error) {
      setError('Erreur lors du chargement du client');
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
      if (isEdit) {
        await axios.put(`${API}/clients/${id}`, formData);
        setSuccess('Client modifié avec succès');
      } else {
        const response = await axios.post(`${API}/clients`, formData);
        setSuccess('Client créé avec succès');
        // Rediriger vers l'edition pour pouvoir ajouter des documents
        setTimeout(() => {
          navigate(`/clients/edit/${response.data.id}`, { replace: true });
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
          onClick={() => navigate('/clients')}
          className="btn btn-secondary"
        >
          <ArrowLeft size={20} />
          Retour
        </button>
        <h1 className="text-3xl font-bold text-gray-900">
          {isEdit ? 'Modifier le client' : 'Nouveau client'}
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
              <h2 className="card-title">Informations générales</h2>
            </div>
            <div className="card-content">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="form-group">
                  <label className="form-label">Nom de l'entreprise / Particulier *</label>
                  <input
                    type="text"
                    name="company_name"
                    value={formData.company_name}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Personne de contact</label>
                  <input
                    type="text"
                    name="contact_person"
                    value={formData.contact_person}
                    onChange={handleChange}
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Email *</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Téléphone *</label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group md:col-span-2">
                  <label className="form-label">Adresse *</label>
                  <input
                    type="text"
                    name="address"
                    value={formData.address}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Ville *</label>
                  <input
                    type="text"
                    name="city"
                    value={formData.city}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Code postal *</label>
                  <input
                    type="text"
                    name="postal_code"
                    value={formData.postal_code}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Pays</label>
                  <input
                    type="text"
                    name="country"
                    value={formData.country}
                    onChange={handleChange}
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Taux de TVA (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    name="vat_rate"
                    value={formData.vat_rate}
                    onChange={handleChange}
                    className="form-input"
                    min="0"
                    max="100"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Informations légales</h2>
            </div>
            <div className="card-content">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="form-group">
                  <label className="form-label">Numéro de TVA intracommunautaire</label>
                  <input
                    type="text"
                    name="intra_vat_number"
                    value={formData.intra_vat_number}
                    onChange={handleChange}
                    className="form-input"
                    placeholder="FR12345678901"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Numéro RCS</label>
                  <input
                    type="text"
                    name="rcs_number"
                    value={formData.rcs_number}
                    onChange={handleChange}
                    className="form-input"
                    placeholder="123 456 789 RCS Paris"
                  />
                </div>

                <div className="form-group md:col-span-2">
                  <label className="form-label">Notes</label>
                  <textarea
                    name="notes"
                    value={formData.notes}
                    onChange={handleChange}
                    className="form-input"
                    rows="3"
                    placeholder="Notes internes sur le client..."
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
              onClick={() => navigate('/clients')}
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
            <ClientDocuments 
              clientId={id} 
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

export default ClientForm;