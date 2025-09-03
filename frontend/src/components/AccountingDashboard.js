import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Calendar, Download, FileText, TrendingUp, Calculator } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AccountingDashboard = () => {
  const [summary, setSummary] = useState(null);
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState({
    start_date: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    fetchAccountingData();
  }, [dateRange]);

  const fetchAccountingData = async () => {
    setLoading(true);
    try {
      const [summaryRes, entriesRes] = await Promise.all([
        axios.get(`${API}/accounting/summary`, {
          params: {
            start_date: dateRange.start_date,
            end_date: dateRange.end_date
          }
        }),
        axios.get(`${API}/accounting/entries`, {
          params: {
            start_date: dateRange.start_date,
            end_date: dateRange.end_date
          }
        })
      ]);
      
      setSummary(summaryRes.data);
      setEntries(entriesRes.data);
    } catch (error) {
      console.error('Erreur lors du chargement des données comptables:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const response = await axios.get(
        format === 'csv' 
          ? `${API}/accounting/export/csv`
          : `${API}/accounting/export/${format}`,
        {
          params: {
            start_date: dateRange.start_date,
            end_date: dateRange.end_date
          },
          responseType: 'blob'
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const filename = format === 'csv' 
        ? `comptabilite_${dateRange.start_date}_${dateRange.end_date}.csv`
        : `comptabilite_${format}_${dateRange.start_date}_${dateRange.end_date}.${format === 'ciel' ? 'txt' : 'csv'}`;
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Erreur lors de l\'export:', error);
    }
  };

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Calculator size={32} />
          Comptabilité
        </h1>
      </div>

      {/* Filtres de date */}
      <div className="card">
        <div className="card-content">
          <div className="flex flex-col md:flex-row gap-4 items-end">
            <div className="form-group">
              <label className="form-label">Date de début</label>
              <input
                type="date"
                value={dateRange.start_date}
                onChange={(e) => setDateRange(prev => ({ ...prev, start_date: e.target.value }))}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Date de fin</label>
              <input
                type="date"
                value={dateRange.end_date}
                onChange={(e) => setDateRange(prev => ({ ...prev, end_date: e.target.value }))}
                className="form-input"
              />
            </div>
            <button
              onClick={fetchAccountingData}
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Chargement...' : 'Actualiser'}
            </button>
          </div>
        </div>
      </div>

      {/* Résumé comptable */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="stat-card">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-number">{summary.summary.total_entries}</div>
                <div className="stat-label">Écritures</div>
              </div>
              <FileText className="text-blue-500" size={40} />
            </div>
          </div>

          <div className="stat-card">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-number">{summary.summary.total_debit.toFixed(2)} €</div>
                <div className="stat-label">Total Débits</div>
              </div>
              <TrendingUp className="text-green-500" size={40} />
            </div>
          </div>

          <div className="stat-card">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-number">{summary.summary.total_credit.toFixed(2)} €</div>
                <div className="stat-label">Total Crédits</div>
              </div>
              <TrendingUp className="text-red-500" size={40} />
            </div>
          </div>
        </div>
      )}

      {/* Statut d'équilibrage */}
      {summary && (
        <div className="card">
          <div className="card-content">
            <div className={`p-4 rounded-lg ${summary.summary.is_balanced ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <div className={`font-semibold ${summary.summary.is_balanced ? 'text-green-800' : 'text-red-800'}`}>
                {summary.summary.is_balanced ? '✅ Écritures équilibrées' : '❌ Écritures déséquilibrées'}
              </div>
              {!summary.summary.is_balanced && (
                <div className="text-red-600 mt-2">
                  Différence: {Math.abs(summary.summary.total_debit - summary.summary.total_credit).toFixed(2)} €
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Boutons d'export */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Exports comptables</h2>
        </div>
        <div className="card-content">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button
              onClick={() => handleExport('csv')}
              className="btn btn-secondary"
            >
              <Download size={16} />
              Export CSV
            </button>
            <button
              onClick={() => handleExport('ciel')}
              className="btn btn-secondary"
            >
              <Download size={16} />
              CIEL Compta
            </button>
            <button
              onClick={() => handleExport('sage')}
              className="btn btn-secondary"
            >
              <Download size={16} />
              SAGE
            </button>
            <button
              onClick={() => handleExport('cegid')}
              className="btn btn-secondary"
            >
              <Download size={16} />
              CEGID
            </button>
          </div>
        </div>
      </div>

      {/* Plan comptable par compte */}
      {summary && Object.keys(summary.accounts).length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Comptes comptables</h2>
          </div>
          <div className="card-content">
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Code compte</th>
                    <th>Libellé</th>
                    <th>Débits</th>
                    <th>Crédits</th>
                    <th>Solde</th>
                    <th>Nb écritures</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(summary.accounts).map(([code, account]) => (
                    <tr key={code}>
                      <td className="font-mono font-medium">{code}</td>
                      <td>{account.account_name}</td>
                      <td className="font-medium text-green-600">
                        {account.total_debit.toFixed(2)} €
                      </td>
                      <td className="font-medium text-red-600">
                        {account.total_credit.toFixed(2)} €
                      </td>
                      <td className={`font-medium ${account.balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {account.balance.toFixed(2)} €
                      </td>
                      <td>
                        <span className="status-badge status-info">
                          {account.entries_count}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Écritures comptables */}
      {entries.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              Journal des écritures ({entries.length})
            </h2>
          </div>
          <div className="card-content">
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Compte</th>
                    <th>Libellé</th>
                    <th>Référence</th>
                    <th>Débit</th>
                    <th>Crédit</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry) => (
                    <tr key={entry.id}>
                      <td>{new Date(entry.entry_date).toLocaleDateString('fr-FR')}</td>
                      <td className="font-mono">{entry.account_code}</td>
                      <td>{entry.account_name}</td>
                      <td className="font-mono">{entry.reference}</td>
                      <td className="font-medium text-green-600">
                        {entry.debit > 0 ? `${entry.debit.toFixed(2)} €` : '-'}
                      </td>
                      <td className="font-medium text-red-600">
                        {entry.credit > 0 ? `${entry.credit.toFixed(2)} €` : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AccountingDashboard;