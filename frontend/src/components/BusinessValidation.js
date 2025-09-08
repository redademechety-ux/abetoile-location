import React, { useState } from 'react';
import axios from 'axios';
import { Search, CheckCircle, XCircle, Building, Loader } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BusinessValidation = ({ onValidData, onError }) => {
  const [identifier, setIdentifier] = useState('');
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [autoFilling, setAutoFilling] = useState(false);

  const handleValidate = async () => {
    if (!identifier.trim()) {
      onError && onError('Veuillez saisir un numéro SIREN ou SIRET');
      return;
    }

    setValidating(true);
    setValidationResult(null);

    try {
      const response = await axios.post(`${API}/validate/business`, {
        identifier: identifier.trim()
      });

      setValidationResult(response.data);
      
      if (!response.data.is_valid) {
        onError && onError('Entreprise non trouvée ou invalide');
      }
    } catch (error) {
      console.error('Erreur validation:', error);
      onError && onError('Erreur lors de la validation');
      setValidationResult({
        is_valid: false,
        validation_errors: ['Erreur de connexion au service de validation']
      });
    } finally {
      setValidating(false);
    }
  };

  const handleAutoFill = async () => {
    if (!validationResult?.is_valid) {
      onError && onError('Veuillez d\'abord valider l\'entreprise');
      return;
    }

    setAutoFilling(true);

    try {
      const response = await axios.post(`${API}/autofill/business`, {
        identifier: identifier.trim()
      });

      if (response.data.success) {
        onValidData && onValidData(response.data.company_data);
      } else {
        onError && onError('Impossible de récupérer les données de l\'entreprise');
      }
    } catch (error) {
      console.error('Erreur auto-fill:', error);
      onError && onError('Erreur lors de la récupération des données');
    } finally {
      setAutoFilling(false);
    }
  };

  const formatIdentifier = (value) => {
    // Remove all non-digits
    const cleaned = value.replace(/\D/g, '');
    
    // Format SIREN (9 digits) or SIRET (14 digits)
    if (cleaned.length <= 9) {
      return cleaned.replace(/(\d{3})(\d{3})(\d{3})/, '$1 $2 $3');
    } else {
      return cleaned.slice(0, 14).replace(/(\d{3})(\d{3})(\d{3})(\d{5})/, '$1 $2 $3 $4');
    }
  };

  const handleIdentifierChange = (e) => {
    const formatted = formatIdentifier(e.target.value);
    setIdentifier(formatted);
    setValidationResult(null);
  };

  return (
    <div className="space-y-4">
      <div className="card">
        <div className="card-header">
          <h3 className="card-title flex items-center gap-2">
            <Building size={20} />
            Validation d'entreprise INSEE
          </h3>
        </div>
        <div className="card-content">
          <div className="space-y-4">
            <div className="form-group">
              <label className="form-label">
                Numéro SIREN (9 chiffres) ou SIRET (14 chiffres)
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={identifier}
                  onChange={handleIdentifierChange}
                  className="form-input font-mono"
                  placeholder="123 456 789 ou 123 456 789 00012"
                  maxLength={17} // For formatted display
                />
                <button
                  onClick={handleValidate}
                  disabled={validating || !identifier.trim()}
                  className="btn btn-primary"
                >
                  {validating ? (
                    <Loader className="animate-spin" size={16} />
                  ) : (
                    <Search size={16} />
                  )}
                  Valider
                </button>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Exemple: 732829320 (SIREN) ou 73282932000074 (SIRET)
              </p>
            </div>

            {validationResult && (
              <div className="space-y-4">
                <div className={`alert ${validationResult.is_valid ? 'alert-success' : 'alert-error'}`}>
                  <div className="flex items-center gap-2">
                    {validationResult.is_valid ? (
                      <CheckCircle size={20} className="text-green-600" />
                    ) : (
                      <XCircle size={20} className="text-red-600" />
                    )}
                    <span>
                      {validationResult.is_valid 
                        ? `Entreprise valide (${validationResult.identifier_type})`
                        : 'Entreprise non trouvée ou invalide'
                      }
                    </span>
                  </div>
                  
                  {validationResult.validation_errors.length > 0 && (
                    <ul className="mt-2 list-disc list-inside text-sm">
                      {validationResult.validation_errors.map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  )}
                </div>

                {validationResult.is_valid && validationResult.company_info && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h4 className="font-medium mb-2">Informations entreprise</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                      {validationResult.company_info.denomination && (
                        <div>
                          <strong>Dénomination:</strong> {validationResult.company_info.denomination}
                        </div>
                      )}
                      {validationResult.company_info.address && (
                        <div>
                          <strong>Adresse:</strong> {validationResult.company_info.address}
                        </div>
                      )}
                      {validationResult.company_info.city && (
                        <div>
                          <strong>Ville:</strong> {validationResult.company_info.postal_code} {validationResult.company_info.city}
                        </div>
                      )}
                      {validationResult.company_info.vat_number && (
                        <div>
                          <strong>N° TVA:</strong> {validationResult.company_info.vat_number}
                        </div>
                      )}
                      {validationResult.company_info.status && (
                        <div>
                          <strong>Statut:</strong> {validationResult.company_info.status === 'A' ? 'Actif' : 'Inactif'}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {validationResult.is_valid && (
                  <div className="flex justify-end">
                    <button
                      onClick={handleAutoFill}
                      disabled={autoFilling}
                      className="btn btn-success"
                    >
                      {autoFilling ? (
                        <>
                          <Loader className="animate-spin mr-2" size={16} />
                          Remplissage...
                        </>
                      ) : (
                        'Remplir automatiquement le formulaire'
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BusinessValidation;