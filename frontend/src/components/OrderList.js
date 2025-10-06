import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Plus, Eye, Search, FileText, Calendar } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const OrderList = () => {
  const [orders, setOrders] = useState([]);
  const [clients, setClients] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [renewalLoading, setRenewalLoading] = useState({});

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [ordersRes, clientsRes, vehiclesRes] = await Promise.all([
        axios.get(`${API}/orders`),
        axios.get(`${API}/clients`),
        axios.get(`${API}/vehicles`)
      ]);
      
      setOrders(ordersRes.data);
      setClients(clientsRes.data);
      setVehicles(vehiclesRes.data);
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error);
    } finally {
      setLoading(false);
    }
  };

  const getClientName = (clientId) => {
    const client = clients.find(c => c.id === clientId);
    return client ? client.company_name : 'Client inconnu';
  };

  const getVehicleName = (vehicleId) => {
    const vehicle = vehicles.find(v => v.id === vehicleId);
    return vehicle ? `${vehicle.brand} ${vehicle.model}` : 'Véhicule inconnu';
  };

  const handleToggleRenewal = async (order) => {
    setRenewalLoading(prev => ({ ...prev, [order.id]: true }));
    setError('');
    setSuccess('');

    try {
      const hasRenewableItems = order.items?.some(item => item.is_renewable);
      const newRenewableStatus = !hasRenewableItems;

      const response = await axios.patch(`${API}/orders/${order.id}/renewal`, {
        is_renewable: newRenewableStatus,
        rental_period: newRenewableStatus ? 'months' : null,
        rental_duration: newRenewableStatus ? 1 : null
      });

      if (response.data.message) {
        // Mettre à jour l'état local
        setOrders(prevOrders => 
          prevOrders.map(o => 
            o.id === order.id 
              ? { 
                  ...o, 
                  items: o.items.map(item => ({ 
                    ...item, 
                    is_renewable: newRenewableStatus 
                  }))
                }
              : o
          )
        );
        
        setSuccess(newRenewableStatus 
          ? 'Reconductibilité activée avec succès' 
          : 'Reconductibilité désactivée avec succès'
        );
      }
    } catch (error) {
      console.error('Erreur lors de la modification de la reconductibilité:', error);
      setError('Erreur lors de la modification de la reconductibilité');
    } finally {
      setRenewalLoading(prev => ({ ...prev, [order.id]: false }));
    }
  };

  const filteredOrders = orders.filter(order => {
    const clientName = getClientName(order.client_id).toLowerCase();
    const orderNumber = order.order_number.toLowerCase();
    return clientName.includes(searchTerm.toLowerCase()) || 
           orderNumber.includes(searchTerm.toLowerCase());
  });

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
        <h1 className="text-3xl font-bold text-gray-900">Gestion des commandes</h1>
        <Link to="/orders/new" className="btn btn-primary">
          <Plus size={20} />
          Nouvelle commande
        </Link>
      </div>

      {/* Messages d'erreur et de succès */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
          {success}
        </div>
      )}

      {/* Barre de recherche */}
      <div className="card">
        <div className="card-content">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Rechercher une commande..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-input pl-10"
            />
          </div>
        </div>
      </div>

      {/* Liste des commandes */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <FileText className="inline mr-2" size={20} />
            Commandes ({filteredOrders.length})
          </h2>
        </div>
        <div className="card-content">
          {filteredOrders.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">Aucune commande trouvée</p>
              <Link to="/orders/new" className="btn btn-primary">
                Créer votre première commande
              </Link>
            </div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>N° Commande</th>
                    <th>Client</th>
                    <th>Date de début</th>
                    <th>Véhicules</th>
                    <th>Total HT</th>
                    <th>Total TTC</th>
                    <th>Statut</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredOrders.map((order) => (
                    <tr key={order.id}>
                      <td className="font-medium font-mono">
                        {order.order_number}
                      </td>
                      <td>{getClientName(order.client_id)}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <Calendar size={16} className="text-gray-400" />
                          {new Date(order.start_date).toLocaleDateString('fr-FR')}
                        </div>
                      </td>
                      <td>
                        <div className="space-y-1">
                          {order.items.map((item, index) => (
                            <div key={index} className="text-sm">
                              {getVehicleName(item.vehicle_id)}
                              {item.is_renewable && (
                                <span className="ml-2 status-badge status-info">
                                  Reconductible
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </td>
                      <td className="font-medium">
                        {order.total_ht.toFixed(2)} €
                      </td>
                      <td className="font-medium">
                        {order.total_ttc.toFixed(2)} €
                      </td>
                      <td>
                        <span className={`status-badge ${
                          order.status === 'active' ? 'status-success' : 'status-warning'
                        }`}>
                          {order.status === 'active' ? 'Active' : 'Terminée'}
                        </span>
                      </td>
                      <td>
                        <div className="flex gap-2">
                          <button
                            onClick={() => alert(`Détails de la commande ${order.order_number}\n\nClient: ${getClientName(order.client_id)}\nDate: ${new Date(order.start_date).toLocaleDateString('fr-FR')}\nTotal TTC: ${order.total_ttc.toFixed(2)}€\nStatut: ${order.status}`)}
                            className="btn btn-sm btn-secondary"
                            title="Voir détails"
                          >
                            <Eye size={16} />
                          </button>
                          <button
                            onClick={() => handleToggleRenewal(order)}
                            disabled={renewalLoading[order.id]}
                            className={`btn btn-sm ${order.items?.some(item => item.is_renewable) ? 'btn-warning' : 'btn-success'}`}
                            title={order.items?.some(item => item.is_renewable) ? 'Désactiver la reconductibilité' : 'Activer la reconductibilité'}
                          >
                            {renewalLoading[order.id] ? (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            ) : (
                              order.items?.some(item => item.is_renewable) ? '🔄❌' : '🔄✅'
                            )}
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

export default OrderList;