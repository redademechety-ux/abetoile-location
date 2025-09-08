import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Plus, Edit, Eye, Search } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ClientList = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await axios.get(`${API}/clients`);
      setClients(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des clients:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredClients = clients.filter(client =>
    client.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.contact_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
        <h1 className="text-3xl font-bold text-gray-900">Gestion des clients</h1>
        <Link to="/clients/new" className="btn btn-primary">
          <Plus size={20} />
          Nouveau client
        </Link>
      </div>

      {/* Barre de recherche */}
      <div className="card">
        <div className="card-content">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Rechercher un client..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-input pl-10"
            />
          </div>
        </div>
      </div>

      {/* Liste des clients */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            Clients ({filteredClients.length})
          </h2>
        </div>
        <div className="card-content">
          {filteredClients.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">Aucun client trouvé</p>
              <Link to="/clients/new" className="btn btn-primary">
                Créer votre premier client
              </Link>
            </div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Entreprise</th>
                    <th>Contact</th>
                    <th>Email</th>
                    <th>Téléphone</th>
                    <th>Ville</th>
                    <th>TVA</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredClients.map((client) => (
                    <tr key={client.id}>
                      <td className="font-medium">{client.company_name}</td>
                      <td>{client.contact_name}</td>
                      <td>
                        <a 
                          href={`mailto:${client.email}`}
                          className="text-blue-600 hover:underline"
                        >
                          {client.email}
                        </a>
                      </td>
                      <td>{client.phone}</td>
                      <td>{client.city}</td>
                      <td>
                        <span className="status-badge status-info">
                          {client.vat_rate}%
                        </span>
                      </td>
                      <td>
                        <div className="flex gap-2">
                          <Link
                            to={`/clients/${client.id}/edit`}
                            className="btn btn-sm btn-secondary"
                            title="Modifier"
                          >
                            <Edit size={16} />
                          </Link>
                          <button
                            onClick={() => alert(`Détails du client\n\nEntreprise: ${client.company_name}\nContact: ${client.contact_name}\nEmail: ${client.email}\nTéléphone: ${client.phone}\nAdresse: ${client.address}\n${client.postal_code} ${client.city}\nTVA: ${client.vat_rate}%\n${client.rcs_number ? `RCS: ${client.rcs_number}` : ''}`)}
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

export default ClientList;