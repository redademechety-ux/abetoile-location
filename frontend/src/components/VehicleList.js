import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Plus, Edit, Eye, Search, Car, AlertTriangle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VehicleList = () => {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchVehicles();
  }, []);

  const fetchVehicles = async () => {
    try {
      const response = await axios.get(`${API}/vehicles`);
      setVehicles(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des véhicules:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredVehicles = vehicles.filter(vehicle =>
    vehicle.brand.toLowerCase().includes(searchTerm.toLowerCase()) ||
    vehicle.model.toLowerCase().includes(searchTerm.toLowerCase()) ||
    vehicle.license_plate.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getVehicleTypeLabel = (type) => {
    const labels = {
      car: 'Voiture',
      van: 'Camionnette',
      truck: 'Camion',
      motorcycle: 'Moto',
      other: 'Autre'
    };
    return labels[type] || type;
  };

  const isControlExpiringSoon = (date) => {
    const expiryDate = new Date(date);
    const today = new Date();
    const daysUntilExpiry = Math.ceil((expiryDate - today) / (1000 * 60 * 60 * 24));
    return daysUntilExpiry <= 30;
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
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Gestion des véhicules</h1>
        <Link to="/vehicles/new" className="btn btn-primary">
          <Plus size={20} />
          Nouveau véhicule
        </Link>
      </div>

      {/* Barre de recherche */}
      <div className="card">
        <div className="card-content">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Rechercher un véhicule..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-input pl-10"
            />
          </div>
        </div>
      </div>

      {/* Liste des véhicules */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <Car className="inline mr-2" size={20} />
            Véhicules ({filteredVehicles.length})
          </h2>
        </div>
        <div className="card-content">
          {filteredVehicles.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">Aucun véhicule trouvé</p>
              <Link to="/vehicles/new" className="btn btn-primary">
                Ajouter votre premier véhicule
              </Link>
            </div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Véhicule</th>
                    <th>Immatriculation</th>
                    <th>Contrôle technique</th>
                    <th>Tarif/jour</th>
                    <th>Disponibilité</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredVehicles.map((vehicle) => (
                    <tr key={vehicle.id}>
                      <td>
                        <span className="status-badge status-info">
                          {getVehicleTypeLabel(vehicle.type)}
                        </span>
                      </td>
                      <td className="font-medium">
                        {vehicle.brand} {vehicle.model}
                      </td>
                      <td className="font-mono">
                        {vehicle.license_plate}
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          {new Date(vehicle.technical_control_expiry).toLocaleDateString('fr-FR')}
                          {isControlExpiringSoon(vehicle.technical_control_expiry) && (
                            <AlertTriangle className="text-amber-500" size={16} title="Expire bientôt" />
                          )}
                        </div>
                      </td>
                      <td className="font-medium">
                        {vehicle.daily_rate.toFixed(2)} €
                      </td>
                      <td>
                        <span className={`status-badge ${vehicle.is_available ? 'status-success' : 'status-danger'}`}>
                          {vehicle.is_available ? 'Disponible' : 'Indisponible'}
                        </span>
                      </td>
                      <td>
                        <div className="flex gap-2">
                          <Link
                            to={`/vehicles/${vehicle.id}/edit`}
                            className="btn btn-sm btn-secondary"
                            title="Modifier"
                          >
                            <Edit size={16} />
                          </Link>
                          <button
                            className="btn btn-sm btn-secondary"
                            title="Voir détails"
                          >
                            <Eye size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VehicleList;