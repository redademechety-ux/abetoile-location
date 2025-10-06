import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { CreditCard, Plus, Trash2, Calendar, DollarSign, FileText, AlertCircle, CheckCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const InvoicePayments = ({ invoice, onPaymentUpdate }) => {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddPayment, setShowAddPayment] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [newPayment, setNewPayment] = useState({
    amount: '',
    payment_date: new Date().toISOString().split('T')[0],
    payment_method: 'bank',
    reference: '',
    notes: ''
  });

  useEffect(() => {
    if (invoice?.id) {
      loadPayments();
    }
  }, [invoice]);

  const loadPayments = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/invoices/${invoice.id}/payments`);
      setPayments(response.data);
    } catch (error) {
      console.error('Erreur chargement paiements:', error);
      setError('Erreur lors du chargement des paiements');
    } finally {
      setLoading(false);
    }
  };

  const handleAddPayment = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError('');
      setSuccess('');

      const paymentData = {
        ...newPayment,
        amount: parseFloat(newPayment.amount),
        payment_date: new Date(newPayment.payment_date).toISOString()
      };

      await axios.post(`${API}/invoices/${invoice.id}/payments`, paymentData);
      
      setSuccess('Paiement ajouté avec succès');
      setShowAddPayment(false);
      setNewPayment({
        amount: '',
        payment_date: new Date().toISOString().split('T')[0],
        payment_method: 'bank',
        reference: '',
        notes: ''
      });
      
      await loadPayments();
      if (onPaymentUpdate) {
        onPaymentUpdate();
      }
    } catch (error) {
      console.error('Erreur ajout paiement:', error);
      setError(error.response?.data?.detail || 'Erreur lors de l\'ajout du paiement');
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePayment = async (paymentId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce paiement ?')) {
      return;
    }

    try {
      setLoading(true);
      setError('');
      await axios.delete(`${API}/payments/${paymentId}`);
      setSuccess('Paiement supprimé avec succès');
      
      await loadPayments();
      if (onPaymentUpdate) {
        onPaymentUpdate();
      }
    } catch (error) {
      console.error('Erreur suppression paiement:', error);
      setError('Erreur lors de la suppression du paiement');
    } finally {
      setLoading(false);
    }
  };

  const getPaymentMethodLabel = (method) => {
    const methods = {
      'bank': 'Virement bancaire',
      'cash': 'Espèces',
      'check': 'Chèque',
      'card': 'Carte bancaire'
    };
    return methods[method] || method;
  };

  const getPaymentStatusColor = () => {
    const remaining = invoice.remaining_amount || invoice.grand_total || invoice.total_ttc;
    if (remaining <= 0) return 'text-green-600 bg-green-50';
    if ((invoice.amount_paid || 0) > 0) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  const getPaymentStatusLabel = () => {
    const remaining = invoice.remaining_amount || invoice.grand_total || invoice.total_ttc;
    if (remaining <= 0) return 'Payée intégralement';
    if ((invoice.amount_paid || 0) > 0) return 'Partiellement payée';
    return 'Non payée';
  };

  const totalAmount = invoice.grand_total || invoice.total_ttc || 0;
  const paidAmount = invoice.amount_paid || 0;
  const remainingAmount = invoice.remaining_amount || (totalAmount - paidAmount);

  return (
    <div className="space-y-6">
      {/* Statut de paiement */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title flex items-center gap-2">
            <CreditCard size={20} />
            Statut de paiement
          </h3>
        </div>
        <div className="card-content">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-sm font-medium text-blue-600">Montant total</div>
              <div className="text-2xl font-bold text-blue-800">
                {totalAmount.toFixed(2)} €
              </div>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm font-medium text-green-600">Montant payé</div>
              <div className="text-2xl font-bold text-green-800">
                {paidAmount.toFixed(2)} €
              </div>
            </div>
            
            <div className={`p-4 rounded-lg ${getPaymentStatusColor()}`}>
              <div className="text-sm font-medium">Reste à payer</div>
              <div className="text-2xl font-bold">
                {remainingAmount.toFixed(2)} €
              </div>
              <div className="text-xs mt-1 flex items-center gap-1">
                {remainingAmount <= 0 ? (
                  <><CheckCircle size={12} /> {getPaymentStatusLabel()}</>
                ) : (
                  <><AlertCircle size={12} /> {getPaymentStatusLabel()}</>
                )}
              </div>
            </div>
          </div>
        </div>
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

      {/* Liste des paiements */}
      <div className="card">
        <div className="card-header">
          <div className="flex items-center justify-between">
            <h3 className="card-title">Historique des paiements</h3>
            {remainingAmount > 0 && (
              <button
                onClick={() => setShowAddPayment(!showAddPayment)}
                className="btn btn-primary btn-sm"
                disabled={loading}
              >
                <Plus size={16} />
                Ajouter un paiement
              </button>
            )}
          </div>
        </div>
        <div className="card-content">
          {loading && (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Chargement...</p>
            </div>
          )}

          {!loading && payments.length === 0 && (
            <div className="text-center py-8">
              <DollarSign size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500 mb-4">Aucun paiement enregistré</p>
              {remainingAmount > 0 && (
                <button
                  onClick={() => setShowAddPayment(true)}
                  className="btn btn-primary"
                >
                  <Plus size={20} />
                  Ajouter le premier paiement
                </button>
              )}
            </div>
          )}

          {!loading && payments.length > 0 && (
            <div className="space-y-3">
              {payments.map((payment) => (
                <div key={payment.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-4">
                        <div>
                          <div className="font-medium text-lg">
                            {payment.amount.toFixed(2)} €
                          </div>
                          <div className="text-sm text-gray-600">
                            {getPaymentMethodLabel(payment.payment_method)}
                          </div>
                        </div>
                        <div>
                          <div className="flex items-center gap-1 text-sm text-gray-600">
                            <Calendar size={14} />
                            {new Date(payment.payment_date).toLocaleDateString('fr-FR')}
                          </div>
                          {payment.reference && (
                            <div className="text-xs text-gray-500">
                              Réf: {payment.reference}
                            </div>
                          )}
                        </div>
                      </div>
                      {payment.notes && (
                        <div className="mt-2 text-sm text-gray-600 bg-gray-50 p-2 rounded">
                          <FileText size={14} className="inline mr-1" />
                          {payment.notes}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => handleDeletePayment(payment.id)}
                      className="btn btn-danger btn-sm"
                      disabled={loading}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Formulaire d'ajout de paiement */}
      {showAddPayment && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Ajouter un paiement</h3>
          </div>
          <div className="card-content">
            <form onSubmit={handleAddPayment} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="form-group">
                  <label className="form-label">Montant (€) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    max={remainingAmount}
                    value={newPayment.amount}
                    onChange={(e) => setNewPayment(prev => ({...prev, amount: e.target.value}))}
                    className="form-input"
                    placeholder={`Max: ${remainingAmount.toFixed(2)}€`}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Date de paiement *</label>
                  <input
                    type="date"
                    value={newPayment.payment_date}
                    onChange={(e) => setNewPayment(prev => ({...prev, payment_date: e.target.value}))}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Mode de paiement *</label>
                  <select
                    value={newPayment.payment_method}
                    onChange={(e) => setNewPayment(prev => ({...prev, payment_method: e.target.value}))}
                    className="form-select"
                    required
                  >
                    <option value="bank">Virement bancaire</option>
                    <option value="cash">Espèces</option>
                    <option value="check">Chèque</option>
                    <option value="card">Carte bancaire</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Référence</label>
                  <input
                    type="text"
                    value={newPayment.reference}
                    onChange={(e) => setNewPayment(prev => ({...prev, reference: e.target.value}))}
                    className="form-input"
                    placeholder="N° transaction, chèque..."
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Notes</label>
                <textarea
                  value={newPayment.notes}
                  onChange={(e) => setNewPayment(prev => ({...prev, notes: e.target.value}))}
                  className="form-input"
                  rows="3"
                  placeholder="Informations complémentaires..."
                />
              </div>

              <div className="flex items-center justify-end gap-4">
                <button
                  type="button"
                  onClick={() => setShowAddPayment(false)}
                  className="btn btn-secondary"
                  disabled={loading}
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading || !newPayment.amount}
                >
                  {loading ? 'Ajout...' : 'Ajouter le paiement'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default InvoicePayments;