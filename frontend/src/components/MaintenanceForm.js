import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Save, 
  ArrowLeft, 
  Upload, 
  FileText, 
  Trash2, 
  Download,
  Calendar,
  DollarSign,
  Car,
  Wrench
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MaintenanceForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [vehicles, setVehicles] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploadingFile, setUploadingFile] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const [formData, setFormData] = useState({
    vehicle_id: '',
    maintenance_type: 'maintenance',
    description: '',
    maintenance_date: new Date().toISOString().split('T')[0],
    amount_ht: 0,
    vat_rate: 20,
    supplier: '',
    notes: ''
  });

  useEffect(() => {
    fetchVehicles();
    if (isEdit) {
      fetchMaintenanceRecord();
      fetchDocuments();
    }
  }, [id]);

  const fetchVehicles = async () => {
    try {
      const response = await axios.get(`${API}/vehicles`);
      setVehicles(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des véhicules:', error);
      setError('Erreur lors du chargement des véhicules');
    }
  };

  const fetchMaintenanceRecord = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/maintenance/${id}`);
      const record = response.data;
      
      setFormData({
        vehicle_id: record.vehicle_id,
        maintenance_type: record.maintenance_type,
        description: record.description,
        maintenance_date: new Date(record.maintenance_date).toISOString().split('T')[0],
        amount_ht: record.amount_ht,
        vat_rate: record.vat_rate,
        supplier: record.supplier || '',
        notes: record.notes || ''
      });
    } catch (error) {
      console.error('Erreur lors du chargement de l\'enregistrement:', error);
      setError('Erreur lors du chargement de l\'enregistrement');
    } finally {
      setLoading(false);
    }
  };

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API}/maintenance/${id}/documents`);
      setDocuments(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des documents:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'amount_ht' || name === 'vat_rate' ? parseFloat(value) || 0 : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const url = isEdit ? `${API}/maintenance/${id}` : `${API}/maintenance`;
      const method = isEdit ? 'put' : 'post';
      
      const dataToSend = {
        ...formData,
        maintenance_date: new Date(formData.maintenance_date).toISOString()
      };

      const response = await axios[method](url, dataToSend);
      
      setSuccess(isEdit ? 'Enregistrement modifié avec succès' : 'Enregistrement créé avec succès');
      
      if (!isEdit) {
        // Rediriger vers la page de détail du nouvel enregistrement
        setTimeout(() => {
          navigate(`/maintenance/${response.data.id}`);
        }, 1500);
      }
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
      setError(error.response?.data?.detail || 'Erreur lors de la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) {
      setSelectedFile(null);
      return;
    }

    console.log('📄 Fichier sélectionné:', file.name, 'Type:', file.type, 'Taille:', file.size);

    // Vérifier le type de fichier
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
    if (!allowedTypes.includes(file.type)) {
      const errorMsg = `Type de fichier non autorisé: ${file.type}. Seuls PDF, JPG et PNG sont acceptés.`;
      console.error('❌', errorMsg);
      setError(errorMsg);
      setSelectedFile(null);
      e.target.value = '';
      return;
    }

    // Vérifier la taille (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      const errorMsg = `Fichier trop volumineux: ${(file.size / 1024 / 1024).toFixed(2)}MB (max 10MB)`;
      console.error('❌', errorMsg);
      setError(errorMsg);
      setSelectedFile(null);
      e.target.value = '';
      return;
    }

    if (!isEdit || !id) {
      const errorMsg = 'Veuillez d\'abord sauvegarder l\'enregistrement avant d\'ajouter des documents.';
      console.error('❌', errorMsg);
      setError(errorMsg);
      setSelectedFile(null);
      e.target.value = '';
      return;
    }

    // Fichier valide, le stocker pour l'upload
    setSelectedFile(file);
    setError(''); // Clear any previous errors
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    setUploadingFile(true);
    setError('');
    setSuccess('');

    try {
      console.log('🚀 Démarrage upload fichier:', selectedFile.name);
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('label', selectedFile.name);

      console.log('📡 Envoi vers:', `${API}/maintenance/${id}/documents`);
      
      // Ne pas définir Content-Type manuellement pour multipart/form-data
      const response = await axios.post(`${API}/maintenance/${id}/documents`, formData);

      console.log('✅ Réponse reçue:', response.status, response.data);
      setSuccess(`Document "${selectedFile.name}" téléchargé avec succès`);
      fetchDocuments(); // Recharger la liste des documents
      
      // Reset le formulaire
      setSelectedFile(null);
      document.querySelector('input[type="file"]').value = '';
    } catch (error) {
      console.error('❌ Erreur lors du téléchargement:', error);
      
      let errorMessage = 'Erreur lors du téléchargement du document';
      
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Data:', error.response.data);
        errorMessage = error.response.data?.detail || `Erreur serveur (${error.response.status})`;
      } else if (error.request) {
        console.error('Pas de réponse du serveur:', error.request);
        errorMessage = 'Pas de réponse du serveur. Vérifiez votre connexion.';
      } else {
        console.error('Erreur de configuration:', error.message);
        errorMessage = `Erreur de configuration: ${error.message}`;
      }
      
      setError(errorMessage);
    } finally {
      setUploadingFile(false);
    }
  };

  const handleDeleteDocument = async (documentId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce document ?')) {
      return;
    }

    try {
      await axios.delete(`${API}/documents/${documentId}`);
      setSuccess('Document supprimé avec succès');
      fetchDocuments(); // Recharger la liste des documents
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      setError('Erreur lors de la suppression du document');
    }
  };

  const handleDownloadDocument = (documentId, filename) => {
    window.open(`${API}/documents/${documentId}/download`, '_blank');
  };

  const calculateVatAmount = () => {
    return formData.amount_ht * (formData.vat_rate / 100);
  };

  const calculateTotalAmount = () => {
    return formData.amount_ht + calculateVatAmount();
  };

  const getVehicleName = (vehicleId) => {
    const vehicle = vehicles.find(v => v.id === vehicleId);
    return vehicle ? `${vehicle.brand} ${vehicle.model} (${vehicle.license_plate})` : '';
  };

  if (loading && isEdit) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/maintenance')}
          className="btn btn-secondary"
        >
          <ArrowLeft size={20} />
          Retour
        </button>
        <h1 className="text-3xl font-bold text-gray-900">
          {isEdit ? 'Modifier l\'enregistrement' : 'Nouvel enregistrement de maintenance'}
        </h1>
      </div>

      {/* Messages */}
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
        {/* Informations principales */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Informations principales</h2>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="form-group">
                <label className="form-label">Véhicule *</label>
                <select
                  name="vehicle_id"
                  value={formData.vehicle_id}
                  onChange={handleChange}
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
                <label className="form-label">Type *</label>
                <select
                  name="maintenance_type"
                  value={formData.maintenance_type}
                  onChange={handleChange}
                  className="form-select"
                  required
                >
                  <option value="maintenance">Entretien</option>
                  <option value="repair">Réparation</option>
                  <option value="inspection">Contrôle</option>
                  <option value="other">Autre</option>
                </select>
              </div>

              <div className="form-group md:col-span-2">
                <label className="form-label">Description *</label>
                <input
                  type="text"
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="Ex: Vidange moteur, Changement plaquettes de frein..."
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Date *</label>
                <input
                  type="date"
                  name="maintenance_date"
                  value={formData.maintenance_date}
                  onChange={handleChange}
                  className="form-input"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Fournisseur/Garage</label>
                <input
                  type="text"
                  name="supplier"
                  value={formData.supplier}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="Nom du garage ou fournisseur"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Informations financières */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Informations financières</h2>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="form-group">
                <label className="form-label">Montant HT (€) *</label>
                <input
                  type="number"
                  name="amount_ht"
                  value={formData.amount_ht}
                  onChange={handleChange}
                  className="form-input"
                  min="0"
                  step="0.01"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Taux TVA (%) *</label>
                <select
                  name="vat_rate"
                  value={formData.vat_rate}
                  onChange={handleChange}
                  className="form-select"
                  required
                >
                  <option value="0">0%</option>
                  <option value="5.5">5,5%</option>
                  <option value="10">10%</option>
                  <option value="20">20%</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Montant TTC (€)</label>
                <div className="form-input bg-gray-50">
                  {calculateTotalAmount().toFixed(2)} €
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  HT: {formData.amount_ht.toFixed(2)} € + TVA: {calculateVatAmount().toFixed(2)} €
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Notes */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Notes complémentaires</h2>
          </div>
          <div className="card-content">
            <div className="form-group">
              <label className="form-label">Notes</label>
              <textarea
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                className="form-input"
                rows="4"
                placeholder="Informations complémentaires, détails techniques, garantie..."
              />
            </div>
          </div>
        </div>

        {/* Documents */}
        {isEdit && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Documents (PDF, JPG, PNG)</h2>
            </div>
            <div className="card-content">
              {/* Upload */}
              <div className="mb-6">
                <label className="form-label">Ajouter un document</label>
                <div className="space-y-3">
                  <div className="flex items-center gap-4">
                    <input
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png"
                      onChange={handleFileUpload}
                      className="form-input"
                      disabled={uploadingFile}
                    />
                    {uploadingFile && (
                      <div className="flex items-center gap-2 text-blue-600">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                        <span className="text-sm">Téléchargement...</span>
                      </div>
                    )}
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded p-3">
                    <p className="text-sm text-blue-800 font-medium mb-1">
                      📄 Instructions d'upload
                    </p>
                    <ul className="text-sm text-blue-700 space-y-1">
                      <li>• Formats acceptés: PDF, JPG, PNG</li>
                      <li>• Taille maximum: 10 MB par fichier</li>
                      <li>• Le document sera lié à cet enregistrement de maintenance</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Liste des documents */}
              {documents.length > 0 ? (
                <div className="space-y-3">
                  {documents.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                      <div className="flex items-center gap-3">
                        <FileText size={20} className="text-blue-600" />
                        <div>
                          <div className="font-medium">{doc.label || doc.filename}</div>
                          <div className="text-sm text-gray-500">
                            {new Date(doc.created_at).toLocaleDateString('fr-FR')} - {(doc.size / 1024).toFixed(1)} KB
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => handleDownloadDocument(doc.id, doc.filename)}
                          className="btn btn-sm btn-secondary"
                          title="Télécharger"
                        >
                          <Download size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteDocument(doc.id)}
                          className="btn btn-sm btn-danger"
                          title="Supprimer"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <FileText size={48} className="mx-auto mb-4 text-gray-300" />
                  <p>Aucun document attaché</p>
                  <p className="text-sm">Téléchargez des factures, photos ou rapports</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/maintenance')}
            className="btn btn-secondary"
          >
            Annuler
          </button>
          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Sauvegarde...
              </>
            ) : (
              <>
                <Save size={20} />
                {isEdit ? 'Mettre à jour' : 'Créer'}
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default MaintenanceForm;