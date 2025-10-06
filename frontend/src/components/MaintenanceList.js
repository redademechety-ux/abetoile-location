import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { 
  Plus, 
  Search, 
  Eye, 
  Edit, 
  Trash2, 
  FileText, 
  Wrench, 
  Settings, 
  Car,
  Calendar,
  DollarSign,
  Upload,
  Download
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MaintenanceList = () => {
  const [maintenanceRecords, setMaintenanceRecords] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedVehicle, setSelectedVehicle] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [maintenanceResponse, vehiclesResponse] = await Promise.all([
        axios.get(`${API}/maintenance`),
        axios.get(`${API}/vehicles`)
      ]);
      
      setMaintenanceRecords(maintenanceResponse.data);
      setVehicles(vehiclesResponse.data);
    } catch (error) {
      console.error('Erreur lors du chargement:', error);
      setError('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (recordId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cet enregistrement de maintenance ?')) {
      return;
    }

    try {
      await axios.delete(`${API}/maintenance/${recordId}`);
      setMaintenanceRecords(prev => prev.filter(record => record.id !== recordId));
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      setError('Erreur lors de la suppression');
    }
  };

  const getVehicleName = (vehicleId) => {
    const vehicle = vehicles.find(v => v.id === vehicleId);
    return vehicle ? `${vehicle.brand} ${vehicle.model} (${vehicle.license_plate})` : 'Véhicule inconnu';
  };

  const getMaintenanceTypeLabel = (type) => {
    const types = {
      'repair': 'Réparation',
      'maintenance': 'Entretien',
      'inspection': 'Contrôle',
      'other': 'Autre'
    };
    return types[type] || type;
  };

  const getMaintenanceTypeIcon = (type) => {
    switch (type) {
      case 'repair':
        return <Settings size={16} className="text-red-600" />;
      case 'maintenance':
        return <Wrench size={16} className="text-blue-600" />;
      case 'inspection':
        return <Eye size={16} className="text-green-600" />;
      default:
        return <FileText size={16} className="text-gray-600" />;
    }
  };

  const filteredRecords = maintenanceRecords.filter(record => {
    const vehicleName = getVehicleName(record.vehicle_id).toLowerCase();
    const description = record.description.toLowerCase();
    const supplier = (record.supplier || '').toLowerCase();
    const searchLower = searchTerm.toLowerCase();
    
    const matchesSearch = vehicleName.includes(searchLower) || 
                         description.includes(searchLower) || 
                         supplier.includes(searchLower);
    
    const matchesVehicle = !selectedVehicle || record.vehicle_id === selectedVehicle;
    
    return matchesSearch && matchesVehicle;
  });

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Maintenance & Réparations</h1>
        <Link to="/maintenance/new" className="btn btn-primary">
          <Plus size={20} />
          Nouvel enregistrement
        </Link>
      </div>

      {/* Messages d'erreur */}
      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {/* Filtres */}
      <div className="card">
        <div className="card-content">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="form-group">
              <label className="form-label">Recherche</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="form-input pl-10"
                  placeholder="Rechercher par véhicule, description ou fournisseur..."
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Filtrer par véhicule</label>
              <select
                value={selectedVehicle}
                onChange={(e) => setSelectedVehicle(e.target.value)}
                className="form-select"
              >
                <option value="">Tous les véhicules</option>
                {vehicles.map(vehicle => (
                  <option key={vehicle.id} value={vehicle.id}>
                    {vehicle.brand} {vehicle.model} - {vehicle.license_plate}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Liste des enregistrements */}
      <div className="card">
        <div className="card-content">
          {filteredRecords.length === 0 ? (
            <div className="text-center py-12">
              <Wrench size={64} className="mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Aucun enregistrement de maintenance
              </h3>
              <p className="text-gray-500 mb-6">
                Commencez par créer votre premier enregistrement de maintenance ou réparation.
              </p>
              <Link to="/maintenance/new" className="btn btn-primary">
                <Plus size={20} />
                Créer un enregistrement
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredRecords.map((record) => (
                <div key={record.id} className="border border-gray-200 rounded-lg p-6 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* En-tête */}
                      <div className="flex items-center gap-3 mb-3">
                        {getMaintenanceTypeIcon(record.maintenance_type)}
                        <span className="font-medium text-lg">
                          {getMaintenanceTypeLabel(record.maintenance_type)}
                        </span>
                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {getVehicleName(record.vehicle_id)}
                        </span>
                      </div>

                      {/* Description */}
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">
                        {record.description}
                      </h3>

                      {/* Détails */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-2">
                          <Calendar size={16} />
                          {new Date(record.maintenance_date).toLocaleDateString('fr-FR')}
                        </div>
                        <div className="flex items-center gap-2">
                          <DollarSign size={16} />
                          {record.amount_ttc.toFixed(2)} € TTC
                        </div>
                        {record.supplier && (
                          <div className="flex items-center gap-2">
                            <Car size={16} />
                            {record.supplier}
                          </div>
                        )}
                      </div>

                      {/* Documents */}
                      {record.documents && record.documents.length > 0 && (
                        <div className="mt-3 flex items-center gap-2 text-sm text-gray-600">
                          <FileText size={16} />
                          {record.documents.length} document{record.documents.length > 1 ? 's' : ''} attaché{record.documents.length > 1 ? 's' : ''}
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 ml-4">
                      <Link
                        to={`/maintenance/${record.id}`}
                        className="btn btn-sm btn-secondary"
                        title="Voir détails"
                      >
                        <Eye size={16} />
                      </Link>
                      <Link
                        to={`/maintenance/${record.id}/edit`}
                        className="btn btn-sm btn-primary"
                        title="Modifier"
                      >
                        <Edit size={16} />
                      </Link>
                      <button
                        onClick={() => handleDelete(record.id)}
                        className="btn btn-sm btn-danger"
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
        </div>
      </div>

      {/* Résumé */}
      {filteredRecords.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Résumé</h3>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {filteredRecords.length}
                </div>
                <div className="text-sm text-gray-600">Enregistrements</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {filteredRecords.filter(r => r.maintenance_type === 'maintenance').length}
                </div>
                <div className="text-sm text-gray-600">Entretiens</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {filteredRecords.filter(r => r.maintenance_type === 'repair').length}
                </div>
                <div className="text-sm text-gray-600">Réparations</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {filteredRecords.reduce((sum, r) => sum + r.amount_ttc, 0).toFixed(0)} €
                </div>
                <div className="text-sm text-gray-600">Total TTC</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MaintenanceList;