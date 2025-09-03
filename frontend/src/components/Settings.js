import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Save, Settings as SettingsIcon, Mail, Building, CreditCard } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Settings = () => {
  const [settings, setSettings] = useState({
    company_name: 'AutoPro Rental',
    company_address: '',
    company_phone: '',
    company_email: '',
    vat_rates: { standard: 20.0, reduced: 10.0, super_reduced: 5.5 },
    payment_delays: { days: 30, weeks: 7, months: 30, years: 365 },
    reminder_periods: [7, 15, 30],
    reminder_templates: {},
    accounting_accounts: {
      sales: '706000',
      vat_standard: '445571',
      vat_reduced: '445572'
    },
    mailgun_api_key: '',
    mailgun_domain: ''
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings({
        ...settings,
        ...response.data,
        mailgun_api_key: response.data.mailgun_api_key || '',
        mailgun_domain: response.data.mailgun_domain || ''
      });
    } catch (error) {
      console.error('Erreur lors du chargement des paramètres:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    if (name.includes('.')) {
      const [parent, child] = name.split('.');
      setSettings(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setSettings(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleVATRateChange = (type, value) => {
    setSettings(prev => ({
      ...prev,
      vat_rates: {
        ...prev.vat_rates,
        [type]: parseFloat(value) || 0
      }
    }));
  };

  const handlePaymentDelayChange = (period, value) => {
    setSettings(prev => ({
      ...prev,
      payment_delays: {
        ...prev.payment_delays,
        [period]: parseInt(value) || 0
      }
    }));
  };

  const handleReminderPeriodsChange = (value) => {
    const periods = value.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p));
    setSettings(prev => ({
      ...prev,
      reminder_periods: periods
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      await axios.put(`${API}/settings`, settings);
      setSuccess('Paramètres sauvegardés avec succès');
    } catch (error) {
      setError(error.response?.data?.detail || 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
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
      <div className="flex items-center gap-4">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <SettingsIcon size={32} />
          Paramètres
        </h1>
      </div>

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

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Informations de l'entreprise */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title flex items-center gap-2">
              <Building size={20} />
              Informations de l'entreprise
            </h2>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="form-group">
                <label className="form-label">Nom de l'entreprise</label>
                <input
                  type="text"
                  name="company_name"
                  value={settings.company_name}
                  onChange={handleChange}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Email</label>
                <input
                  type="email"
                  name="company_email"
                  value={settings.company_email}
                  onChange={handleChange}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Téléphone</label>
                <input
                  type="tel"
                  name="company_phone"
                  value={settings.company_phone}
                  onChange={handleChange}
                  className="form-input"
                />
              </div>

              <div className="form-group md:col-span-2">
                <label className="form-label">Adresse</label>
                <textarea
                  name="company_address"
                  value={settings.company_address}
                  onChange={handleChange}
                  className="form-textarea"
                  rows="3"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Taux de TVA */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title flex items-center gap-2">
              <CreditCard size={20} />
              Taux de TVA
            </h2>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="form-group">
                <label className="form-label">TVA Standard (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={settings.vat_rates.standard}
                  onChange={(e) => handleVATRateChange('standard', e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">TVA Réduite (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={settings.vat_rates.reduced}
                  onChange={(e) => handleVATRateChange('reduced', e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">TVA Super Réduite (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={settings.vat_rates.super_reduced}
                  onChange={(e) => handleVATRateChange('super_reduced', e.target.value)}
                  className="form-input"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Délais de paiement */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Délais de paiement (jours)</h2>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="form-group">
                <label className="form-label">Location journalière</label>
                <input
                  type="number"
                  value={settings.payment_delays.days}
                  onChange={(e) => handlePaymentDelayChange('days', e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Location hebdomadaire</label>
                <input
                  type="number"
                  value={settings.payment_delays.weeks}
                  onChange={(e) => handlePaymentDelayChange('weeks', e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Location mensuelle</label>
                <input
                  type="number"
                  value={settings.payment_delays.months}
                  onChange={(e) => handlePaymentDelayChange('months', e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Location annuelle</label>
                <input
                  type="number"
                  value={settings.payment_delays.years}
                  onChange={(e) => handlePaymentDelayChange('years', e.target.value)}
                  className="form-input"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Relances automatiques */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Relances automatiques</h2>
          </div>
          <div className="card-content">
            <div className="form-group">
              <label className="form-label">
                Périodes de relance (jours après échéance, séparés par des virgules)
              </label>
              <input
                type="text"
                value={settings.reminder_periods.join(', ')}
                onChange={(e) => handleReminderPeriodsChange(e.target.value)}
                className="form-input"
                placeholder="7, 15, 30"
              />
              <p className="text-sm text-gray-500 mt-1">
                Exemple : 7, 15, 30 enverra des relances à 7, 15 et 30 jours après l'échéance
              </p>
            </div>
          </div>
        </div>

        {/* Configuration email */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title flex items-center gap-2">
              <Mail size={20} />
              Configuration Mailgun
            </h2>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="form-group">
                <label className="form-label">Clé API Mailgun</label>
                <input
                  type="password"
                  name="mailgun_api_key"
                  value={settings.mailgun_api_key}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="key-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Domaine Mailgun</label>
                <input
                  type="text"
                  name="mailgun_domain"
                  value={settings.mailgun_domain}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="mg.votre-domaine.com"
                />
              </div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-blue-800 text-sm">
                <strong>Info :</strong> Pour configurer Mailgun, créez un compte sur mailgun.com 
                et obtenez votre clé API et votre domaine. Ces informations sont nécessaires 
                pour l'envoi automatique des factures et relances.
              </p>
            </div>
          </div>
        </div>

        {/* Comptes comptables */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Comptes comptables</h2>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="form-group">
                <label className="form-label">Compte de vente</label>
                <input
                  type="text"
                  name="accounting_accounts.sales"
                  value={settings.accounting_accounts.sales}
                  onChange={handleChange}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Compte TVA standard</label>
                <input
                  type="text"
                  name="accounting_accounts.vat_standard"
                  value={settings.accounting_accounts.vat_standard}
                  onChange={handleChange}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Compte TVA réduite</label>
                <input
                  type="text"
                  name="accounting_accounts.vat_reduced"
                  value={settings.accounting_accounts.vat_reduced}
                  onChange={handleChange}
                  className="form-input"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-4">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={saving}
          >
            {saving ? (
              <span className="loading-spinner"></span>
            ) : (
              <>
                <Save size={20} />
                Sauvegarder
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default Settings;