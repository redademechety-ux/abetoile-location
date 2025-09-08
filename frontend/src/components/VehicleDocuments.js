import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, FileText, Eye, Download, Trash2, Edit, Plus, X } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VehicleDocuments = ({ vehicleId, onDocumentUpdate }) => {
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingDocument, setEditingDocument] = useState(null);
  const [newDocumentLabel, setNewDocumentLabel] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);

  useEffect(() => {
    if (vehicleId) {
      fetchDocuments();
    }
  }, [vehicleId]);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/vehicles/${vehicleId}/documents`);
      setDocuments(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des documents:', error);
      if (error.response?.status !== 404) {
        setError('Erreur lors du chargement des documents');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Vérifier la taille du fichier (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setError('Le fichier est trop volumineux (max 10MB)');
        return;
      }
      
      // Vérifier le type de fichier
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
      if (!allowedTypes.includes(file.type)) {
        setError('Format de fichier non supporté. Utilisez JPG, PNG, GIF ou PDF');
        return;
      }
      
      setSelectedFile(file);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !newDocumentLabel.trim()) {
      setError('Veuillez sélectionner un fichier et saisir un libellé');
      return;
    }

    setUploading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('label', newDocumentLabel.trim());
      formData.append('document_type', getDocumentType(newDocumentLabel));

      const response = await axios.post(
        `${API}/vehicles/${vehicleId}/documents/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setSuccess('Document uploadé avec succès');
      setDocuments(prev => [...prev, response.data]);
      resetForm();
      setShowAddModal(false);
      
      if (onDocumentUpdate) {
        onDocumentUpdate();
      }
    } catch (error) {
      setError(error.response?.data?.detail || 'Erreur lors de l\'upload');
    } finally {
      setUploading(false);
    }
  };

  const getDocumentType = (label) => {
    const lowerLabel = label.toLowerCase();
    if (lowerLabel.includes('carte grise') || lowerLabel.includes('certificat d\'immatriculation')) {
      return 'registration_card';
    } else if (lowerLabel.includes('assurance')) {
      return 'insurance';
    } else if (lowerLabel.includes('contrôle technique')) {
      return 'technical_control';
    }
    return 'other';
  };

  const handleDelete = async (documentId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce document ?')) {
      return;
    }

    try {
      await axios.delete(`${API}/vehicles/${vehicleId}/documents/${documentId}`);
      setDocuments(prev => prev.filter(doc => doc.id !== documentId));
      setSuccess('Document supprimé avec succès');
      
      if (onDocumentUpdate) {
        onDocumentUpdate();
      }
    } catch (error) {
      setError(error.response?.data?.detail || 'Erreur lors de la suppression');
    }
  };

  const handleUpdateLabel = async (documentId, newLabel) => {
    try {
      const response = await axios.put(`${API}/vehicles/${vehicleId}/documents/${documentId}`, {
        label: newLabel.trim()
      });
      
      setDocuments(prev => prev.map(doc => 
        doc.id === documentId ? { ...doc, label: newLabel.trim() } : doc
      ));
      setEditingDocument(null);
      setSuccess('Libellé mis à jour avec succès');
    } catch (error) {
      setError(error.response?.data?.detail || 'Erreur lors de la mise à jour');
    }
  };

  const handleView = async (documentId) => {
    try {
      const response = await axios.get(`${API}/vehicles/${vehicleId}/documents/${documentId}/view`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
      
      // Nettoyer l'URL après un délai
      setTimeout(() => window.URL.revokeObjectURL(url), 1000);
    } catch (error) {
      setError('Erreur lors de l\'ouverture du document');
    }
  };

  const handleDownload = async (documentId, filename) => {
    try {
      const response = await axios.get(`${API}/vehicles/${vehicleId}/documents/${documentId}/download`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setError('Erreur lors du téléchargement');
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    setNewDocumentLabel('');
    setError('');
  };

  const getDocumentIcon = (documentType) => {
    switch (documentType) {
      case 'registration_card':
        return '🚗';
      case 'insurance':
        return '🛡️';
      case 'technical_control':
        return '🔧';
      default:
        return '📄';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="alert alert-error">
          <span>{error}</span>
          <button onClick={() => setError('')} className="ml-auto">
            <X size={16} />
          </button>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          <span>{success}</span>
          <button onClick={() => setSuccess('')} className="ml-auto">
            <X size={16} />
          </button>
        </div>
      )}

      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Documents du véhicule</h3>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn btn-primary btn-sm"
          disabled={uploading}
        >
          <Plus size={16} />
          Ajouter un document
        </button>
      </div>

      {documents.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <FileText size={48} className="mx-auto mb-4 text-gray-300" />
          <p>Aucun document uploadé</p>
          <p className="text-sm">Cliquez sur "Ajouter un document" pour commencer</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {documents.map((doc) => (
            <div key={doc.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{getDocumentIcon(doc.document_type)}</span>
                  <div>
                    {editingDocument === doc.id ? (
                      <div className="flex items-center space-x-2">
                        <input
                          type="text"
                          defaultValue={doc.label}
                          className="form-input text-sm"
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') {
                              handleUpdateLabel(doc.id, e.target.value);
                            }
                          }}
                          onBlur={(e) => handleUpdateLabel(doc.id, e.target.value)}
                          autoFocus
                        />
                      </div>
                    ) : (
                      <div>
                        <p className="font-medium">{doc.label}</p>
                        <p className="text-sm text-gray-500">
                          {doc.filename} • {(doc.file_size / 1024).toFixed(1)} Ko • 
                          Uploadé le {new Date(doc.uploaded_at).toLocaleDateString('fr-FR')}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleView(doc.id)}
                    className="btn btn-ghost btn-sm"
                    title="Voir le document"
                  >
                    <Eye size={16} />
                  </button>
                  <button
                    onClick={() => handleDownload(doc.id, doc.filename)}
                    className="btn btn-ghost btn-sm"
                    title="Télécharger"
                  >
                    <Download size={16} />
                  </button>
                  <button
                    onClick={() => setEditingDocument(editingDocument === doc.id ? null : doc.id)}
                    className="btn btn-ghost btn-sm"
                    title="Modifier le libellé"
                  >
                    <Edit size={16} />
                  </button>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="btn btn-ghost btn-sm text-red-600 hover:text-red-700"
                    title="Supprimer"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal d'ajout de document */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Ajouter un document</h3>
              <button
                onClick={() => {
                  setShowAddModal(false);
                  resetForm();
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="form-label">Libellé du document *</label>
                <input
                  type="text"
                  value={newDocumentLabel}
                  onChange={(e) => setNewDocumentLabel(e.target.value)}
                  className="form-input"
                  placeholder="Ex: Carte grise recto, Assurance 2024..."
                  required
                />
              </div>

              <div>
                <label className="form-label">Fichier *</label>
                <input
                  type="file"
                  onChange={handleFileSelect}
                  className="form-input"
                  accept=".pdf,.jpg,.jpeg,.png,.gif"
                  required
                />
                <p className="text-sm text-gray-500 mt-1">
                  Formats acceptés: PDF, JPG, PNG, GIF (max 10MB)
                </p>
              </div>

              {selectedFile && (
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-sm">
                    <strong>Fichier sélectionné:</strong> {selectedFile.name}
                  </p>
                  <p className="text-sm text-gray-600">
                    Taille: {(selectedFile.size / 1024).toFixed(1)} Ko
                  </p>
                </div>
              )}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowAddModal(false);
                  resetForm();
                }}
                className="btn btn-secondary"
                disabled={uploading}
              >
                Annuler
              </button>
              <button
                onClick={handleUpload}
                className="btn btn-primary"
                disabled={uploading || !selectedFile || !newDocumentLabel.trim()}
              >
                {uploading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Upload...
                  </>
                ) : (
                  <>
                    <Upload size={16} className="mr-2" />
                    Uploader
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VehicleDocuments;