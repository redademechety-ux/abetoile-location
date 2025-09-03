import React, { useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Login = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    full_name: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const payload = isLogin 
        ? { username: formData.username, password: formData.password }
        : formData;

      const response = await axios.post(`${API}${endpoint}`, payload);
      
      if (isLogin) {
        onLogin(response.data.access_token);
      } else {
        // After registration, automatically login
        const loginResponse = await axios.post(`${API}/auth/login`, {
          username: formData.username,
          password: formData.password
        });
        onLogin(loginResponse.data.access_token);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1 className="login-title">
          {isLogin ? 'Connexion' : 'Inscription'}
        </h1>
        
        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Nom d'utilisateur</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              className="form-input"
              required
            />
          </div>

          {!isLogin && (
            <>
              <div className="form-group">
                <label className="form-label">Email</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="form-input"
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Nom complet</label>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  className="form-input"
                  required
                />
              </div>
            </>
          )}

          <div className="form-group">
            <label className="form-label">Mot de passe</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="form-input"
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginBottom: '1rem' }}
            disabled={loading}
          >
            {loading ? (
              <span className="loading-spinner"></span>
            ) : (
              isLogin ? 'Se connecter' : 'S\'inscrire'
            )}
          </button>
        </form>

        <div style={{ textAlign: 'center' }}>
          <button
            type="button"
            onClick={() => setIsLogin(!isLogin)}
            className="btn btn-secondary"
            style={{ background: 'none', border: 'none', color: '#6366f1', textDecoration: 'underline' }}
          >
            {isLogin ? 'Créer un compte' : 'Déjà un compte ? Se connecter'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;