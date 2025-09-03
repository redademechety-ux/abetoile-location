import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Receipt, Download, CheckCircle, AlertTriangle, FileText, Loader } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const InvoiceList = () => {
  const [invoices, setInvoices] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');
  const [generatingPdf, setGeneratingPdf] = useState({});

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [invoicesRes, clientsRes] = await Promise.all([
        axios.get(`${API}/invoices`),
        axios.get(`${API}/clients`)
      ]);
      
      setInvoices(invoicesRes.data);
      setClients(clientsRes.data);
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

  const getStatusLabel = (status) => {
    const labels = {
      draft: 'Brouillon',
      sent: 'Envoyée',
      paid: 'Payée',
      overdue: 'En retard',
      cancelled: 'Annulée'
    };
    return labels[status] || status;
  };

  const getStatusBadgeClass = (status) => {
    const classes = {
      draft: 'status-warning',
      sent: 'status-info',
      paid: 'status-success',
      overdue: 'status-danger',
      cancelled: 'status-danger'
    };
    return classes[status] || 'status-info';
  };

  const isOverdue = (invoice) => {
    if (invoice.status === 'paid' || invoice.status === 'cancelled') return false;
    return new Date(invoice.due_date) < new Date();
  };

  const markAsPaid = async (invoiceId) => {
    try {
      await axios.put(`${API}/invoices/${invoiceId}/mark-paid`);
      // Refresh data
      fetchData();
    } catch (error) {
      console.error('Erreur lors du marquage comme payée:', error);
    }
  };

  const generatePdf = async (invoiceId) => {
    setGeneratingPdf(prev => ({ ...prev, [invoiceId]: true }));
    try {
      const response = await axios.post(`${API}/invoices/${invoiceId}/generate-pdf`);
      
      if (response.data.pdf_data) {
        // Auto-download the PDF
        const pdfBytes = atob(response.data.pdf_data);
        const pdfArray = new Uint8Array(pdfBytes.length);
        for (let i = 0; i < pdfBytes.length; i++) {
          pdfArray[i] = pdfBytes.charCodeAt(i);
        }
        
        const blob = new Blob([pdfArray], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        
        const invoice = invoices.find(inv => inv.id === invoiceId);
        link.setAttribute('download', `facture_${invoice?.invoice_number || invoiceId}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        
        // Refresh invoice list to update status
        fetchData();
      }
    } catch (error) {
      console.error('Erreur lors de la génération du PDF:', error);
      alert('Erreur lors de la génération du PDF. Veuillez réessayer.');
    } finally {
      setGeneratingPdf(prev => ({ ...prev, [invoiceId]: false }));
    }
  };

  const downloadPdf = async (invoiceId) => {
    try {
      const response = await axios.get(`${API}/invoices/${invoiceId}/download-pdf`, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const invoice = invoices.find(inv => inv.id === invoiceId);
      link.setAttribute('download', `facture_${invoice?.invoice_number || invoiceId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Erreur lors du téléchargement du PDF:', error);
      alert('PDF non trouvé ou erreur de téléchargement.');
    }
  };

  const filteredInvoices = invoices.filter(invoice => {
    const clientName = getClientName(invoice.client_id).toLowerCase();
    const invoiceNumber = invoice.invoice_number.toLowerCase();
    const matchesSearch = clientName.includes(searchTerm.toLowerCase()) || 
                         invoiceNumber.includes(searchTerm.toLowerCase());

    if (filter === 'all') return matchesSearch;
    if (filter === 'overdue') return matchesSearch && isOverdue(invoice);
    if (filter === 'paid') return matchesSearch && invoice.status === 'paid';
    if (filter === 'unpaid') return matchesSearch && invoice.status !== 'paid' && invoice.status !== 'cancelled';
    
    return matchesSearch;
  });

  const getFilterCounts = () => {
    return {
      all: invoices.length,
      overdue: invoices.filter(isOverdue).length,
      paid: invoices.filter(i => i.status === 'paid').length,
      unpaid: invoices.filter(i => i.status !== 'paid' && i.status !== 'cancelled').length
    };
  };

  const counts = getFilterCounts();

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
        <h1 className="text-3xl font-bold text-gray-900">Gestion des factures</h1>
        <div className="text-sm text-gray-500">
          {counts.overdue > 0 && (
            <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full">
              {counts.overdue} facture(s) en retard
            </span>
          )}
        </div>
      </div>

      {/* Filtres */}
      <div className="card">
        <div className="card-content">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Rechercher une facture..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="form-input pl-10"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setFilter('all')}
                className={`btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
              >
                Toutes ({counts.all})
              </button>
              <button
                onClick={() => setFilter('overdue')}
                className={`btn btn-sm ${filter === 'overdue' ? 'btn-danger' : 'btn-secondary'}`}
              >
                En retard ({counts.overdue})
              </button>
              <button
                onClick={() => setFilter('unpaid')}
                className={`btn btn-sm ${filter === 'unpaid' ? 'btn-primary' : 'btn-secondary'}`}
              >
                Impayées ({counts.unpaid})
              </button>
              <button
                onClick={() => setFilter('paid')}
                className={`btn btn-sm ${filter === 'paid' ? 'btn-success' : 'btn-secondary'}`}
              >
                Payées ({counts.paid})
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Liste des factures */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <Receipt className="inline mr-2" size={20} />
            Factures ({filteredInvoices.length})
          </h2>
        </div>
        <div className="card-content">
          {filteredInvoices.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">Aucune facture trouvée</p>
            </div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>N° Facture</th>
                    <th>Client</th>
                    <th>Date</th>
                    <th>Échéance</th>
                    <th>Montant TTC</th>
                    <th>Statut</th>
                    <th>PDF</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredInvoices.map((invoice) => (
                    <tr key={invoice.id} className={isOverdue(invoice) ? 'bg-red-50' : ''}>
                      <td className="font-medium font-mono">
                        {invoice.invoice_number}
                        {isOverdue(invoice) && (
                          <AlertTriangle className="inline ml-2 text-red-500" size={16} />
                        )}
                      </td>
                      <td>{getClientName(invoice.client_id)}</td>
                      <td>{new Date(invoice.invoice_date).toLocaleDateString('fr-FR')}</td>
                      <td>
                        <span className={isOverdue(invoice) ? 'text-red-600 font-medium' : ''}>
                          {new Date(invoice.due_date).toLocaleDateString('fr-FR')}
                        </span>
                      </td>
                      <td className="font-medium">
                        {invoice.total_ttc.toFixed(2)} €
                      </td>
                      <td>
                        <span className={`status-badge ${getStatusBadgeClass(invoice.status)}`}>
                          {getStatusLabel(invoice.status)}
                        </span>
                      </td>
                      <td>
                        {invoice.pdf_data ? (
                          <button
                            onClick={() => downloadPdf(invoice.id)}
                            className="btn btn-sm btn-secondary"
                            title="Télécharger PDF existant"
                          >
                            <Download size={16} />
                          </button>
                        ) : (
                          <button
                            onClick={() => generatePdf(invoice.id)}
                            className="btn btn-sm btn-primary"
                            disabled={generatingPdf[invoice.id]}
                            title="Générer PDF avec IA"
                          >
                            {generatingPdf[invoice.id] ? (
                              <Loader className="animate-spin" size={16} />
                            ) : (
                              <FileText size={16} />
                            )}
                          </button>
                        )}
                      </td>
                      <td>
                        <div className="flex gap-2">
                          {invoice.status !== 'paid' && invoice.status !== 'cancelled' && (
                            <button
                              onClick={() => markAsPaid(invoice.id)}
                              className="btn btn-sm btn-success"
                              title="Marquer comme payée"
                            >
                              <CheckCircle size={16} />
                            </button>
                          )}
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

export default InvoiceList;