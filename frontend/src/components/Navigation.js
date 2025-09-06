import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Car, Users, FileText, Receipt, Settings, LogOut, BarChart3, Calculator } from 'lucide-react';

const Navigation = ({ onLogout }) => {
  const location = useLocation();

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === path;
    }
    return location.pathname.startsWith(path);
  };

  const navItems = [
    { path: '/', label: 'Tableau de bord', icon: BarChart3 },
    { path: '/clients', label: 'Clients', icon: Users },
    { path: '/vehicles', label: 'Véhicules', icon: Car },
    { path: '/orders', label: 'Commandes', icon: FileText },
    { path: '/invoices', label: 'Factures', icon: Receipt },
    { path: '/accounting', label: 'Comptabilité', icon: Calculator },
    { path: '/settings', label: 'Paramètres', icon: Settings }
  ];

  return (
    <nav className="nav-container">
      <div className="nav-content">
        <Link to="/" className="logo">
          <Car className="inline mr-2" size={24} />
          Abetoile Location
        </Link>
        
        <ul className="nav-links">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={isActive(item.path) ? 'active' : ''}
                >
                  <Icon size={18} className="inline mr-1" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>

        <button onClick={onLogout} className="logout-btn">
          <LogOut size={18} className="inline mr-1" />
          Déconnexion
        </button>
      </div>
    </nav>
  );
};

export default Navigation;