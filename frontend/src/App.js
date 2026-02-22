import React, { useState, useEffect } from 'react';
import Auth from './components/Auth';
import Notes from './components/notes';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(null);
  const [verifying, setVerifying] = useState(!!localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      setVerifying(true);
      // Verify token and get user info
      fetch(`${API_URL}/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
        .then(res => {
          if (res.ok) return res.json();
          throw new Error('Invalid token');
        })
        .then(data => {
          setUser(data);
          setVerifying(false);
        })
        .catch(() => {
          // Token invalid, clear it
          logout();
          setVerifying(false);
        });
    } else {
      setVerifying(false);
    }
  }, [token]);

  const login = (newToken, username) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setUser({ username });
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  if (verifying) {
    return (
      <div className="app">
        <div className="loading-screen">Verifying session...</div>
      </div>
    );
  }

  return (
    <div className="app">
      {!token ? (
        <Auth onLogin={login} apiUrl={API_URL} />
      ) : (
        <Notes
          token={token}
          user={user}
          onLogout={logout}
          apiUrl={API_URL}
        />
      )}
    </div>
  );
}

export default App;
