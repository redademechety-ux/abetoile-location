import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { AlertTriangle, Users, Car, FileText, Receipt } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    overdue_invoices: 0,
    active_orders: 0,
    total_clients: 0,
    total_vehicles: 0
  });
  const [overdueInvoices, setOverdueInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    fetchOverdueInvoices();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement du tableau de bord:', error);
    }
  };

  const fetchOverdueInvoices = async () => {
    try {
      const response = await axios.get(`${API}/invoices/overdue`);
      setOverdueInvoices(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des factures impayées:', error);
    } finally {
      setLoading(false);
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
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Tableau de bord</h1>
        <div className="text-sm text-gray-500">
          Dernière mise à jour: {new Date().toLocaleString('fr-FR')}
        </div>
      </div>

      {/* Alertes factures impayées */}
      {dashboardData.overdue_invoices > 0 && (
        <div className="alert alert-warning">
          <AlertTriangle className="inline mr-2" size={20} />
          <strong>Attention !</strong> Vous avez {dashboardData.overdue_invoices} facture(s) en retard de paiement.
        </div>
      )}

      {/* Statistiques principales */}
      <div className="dashboard-grid">
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <div className="stat-number">{dashboardData.total_clients}</div>
              <div className="stat-label">Clients actifs</div>
            </div>
            <Users className="text-blue-500" size={40} />
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <div className="stat-number">{dashboardData.total_vehicles}</div>
              <div className="stat-label">Véhicules</div>
            </div>
            <Car className="text-green-500" size={40} />
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <div className="stat-number">{dashboardData.active_orders}</div>
              <div className="stat-label">Commandes actives</div>
            </div>
            <FileText className="text-purple-500" size={40} />
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <div className="stat-number text-red-600">{dashboardData.overdue_invoices}</div>
              <div className="stat-label">Factures impayées</div>
            </div>
            <Receipt className="text-red-500" size={40} />
          </div>
        </div>
      </div>

      {/* Liste des factures impayées */}
      {overdueInvoices.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title text-red-600">
              <AlertTriangle className="inline mr-2" size={20} />
              Factures en retard de paiement
            </h2>
          </div>
          <div className="card-content">
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>N° Facture</th>
                    <th>Client</th>
                    <th>Montant TTC</th>
                    <th>Date d'échéance</th>
                    <th>Retard (jours)</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {overdueInvoices.map((invoice) => {
                    const daysOverdue = Math.ceil(
                      (new Date() - new Date(invoice.due_date)) / (1000 * 60 * 60 * 24)
                    );
                    return (
                      <tr key={invoice.id}>
                        <td className="font-medium">{invoice.invoice_number}</td>
                        <td>{invoice.client_id}</td>
                        <td className="font-medium">{invoice.total_ttc.toFixed(2)} €</td>
                        <td>{new Date(invoice.due_date).toLocaleDateString('fr-FR')}</td>
                        <td>
                          <span className="status-badge status-danger">
                            {daysOverdue} jours
                          </span>
                        </td>
                        <td>
                          <button className="btn btn-sm btn-danger">
                            Relancer
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Actions rapides */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="card-content text-center">
            <Users className="mx-auto mb-4 text-blue-500" size={48} />
            <h3 className="font-semibold mb-2">Nouveau client</h3>
            <p className="text-gray-600 mb-4">Ajouter un nouveau client au système</p>
            <a href="/clients/new" className="btn btn-primary">
              Créer un client
            </a>
          </div>
        </div>

        <div className="card">
          <div className="card-content text-center">
            <Car className="mx-auto mb-4 text-green-500" size={48} />
            <h3 className="font-semibold mb-2">Nouveau véhicule</h3>
            <p className="text-gray-600 mb-4">Ajouter un véhicule à votre flotte</p>
            <a href="/vehicles/new" className="btn btn-success">
              Ajouter un véhicule
            </a>
          </div>
        </div>

        <div className="card">
          <div className="card-content text-center">
            <FileText className="mx-auto mb-4 text-purple-500" size={48} />
            <h3 className="font-semibold mb-2">Nouvelle commande</h3>
            <p className="text-gray-600 mb-4">Créer une nouvelle commande de location</p>
            <a href="/orders/new" className="btn btn-primary">
              Nouvelle commande
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;