import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Save, ArrowLeft, Upload } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ClientForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = !!id;

  const [formData, setFormData] = useState({
    company_name: '',
    contact_name: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    postal_code: '',
    country: 'France',
    vat_rate: 20.0,
    vat_number: '',
    rcs_number: ''
  });

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

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
        await axios.post(`${API}/clients`, formData);
        setSuccess('Client créé avec succès');
      }
      
      setTimeout(() => {
        navigate('/clients');
      }, 1500);
    } catch (error) {
      setError(error.response?.data?.detail || 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  const validateRCS = async () => {
    if (!formData.rcs_number) return;
    
    // Simulation de validation RCS (en attendant l'API INSEE)
    alert('Validation RCS : Fonctionnalité disponible avec l\'API INSEE/Infogreffe');
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

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Informations générales</h2>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="form-group">
                <label className="form-label">Nom de l'entreprise *</label>
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
                <label className="form-label">Nom du contact *</label>
                <input
                  type="text"
                  name="contact_name"
                  value={formData.contact_name}
                  onChange={handleChange}
                  className="form-input"
                  required
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
                <select
                  name="country"
                  value={formData.country}
                  onChange={handleChange}
                  className="form-select"
                >
                  <option value="France">France</option>
                  <option value="Belgique">Belgique</option>
                  <option value="Suisse">Suisse</option>
                  <option value="Luxembourg">Luxembourg</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Taux de TVA (%)</label>
                <input
                  type="number"
                  step="0.1"
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
            <h2 className="card-title">Informations fiscales</h2>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="form-group">
                <label className="form-label">Numéro de TVA intracommunautaire</label>
                <input
                  type="text"
                  name="vat_number"
                  value={formData.vat_number}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="FR12345678901"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Numéro RCS</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    name="rcs_number"
                    value={formData.rcs_number}
                    onChange={handleChange}
                    className="form-input"
                    placeholder="123 456 789 R.C.S. Paris"
                  />
                  <button
                    type="button"
                    onClick={validateRCS}
                    className="btn btn-secondary"
                    disabled={!formData.rcs_number}
                  >
                    Vérifier
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Documents</h2>
          </div>
          <div className="card-content">
            <div className="space-y-4">
              <div>
                <label className="form-label">Permis de conduire et pièce d'identité</label>
                <div className="border-dashed border-2 border-gray-300 rounded-lg p-6 text-center">
                  <Upload className="mx-auto mb-2 text-gray-400" size={48} />
                  <p className="text-gray-600">
                    Glissez vos fichiers ici ou cliquez pour sélectionner
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Formats acceptés: PDF, JPG, PNG (max 10MB)
                  </p>
                  <input
                    type="file"
                    multiple
                    accept=".pdf,.jpg,.jpeg,.png"
                    className="hidden"
                    onChange={(e) => {
                      // TODO: Gérer l'upload des fichiers
                      console.log('Fichiers sélectionnés:', e.target.files);
                    }}
                  />
                </div>
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
              <span className="loading-spinner"></span>
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
    </div>
  );
};

export default ClientForm;