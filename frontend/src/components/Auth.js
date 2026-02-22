import React, { useState } from 'react';

function Auth({ onLogin, apiUrl }) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const validateForm = () => {
    if (!formData.username.trim()) {
      setError('Username is required.');
      return false;
    }
    if (formData.username.trim().length < 3) {
      setError('Username must be at least 3 characters.');
      return false;
    }
    if (!formData.password) {
      setError('Password is required.');
      return false;
    }
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters.');
      return false;
    }
    if (!isLogin && formData.password !== confirmPassword) {
      setError('Passwords do not match.');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!validateForm()) return;

    setLoading(true);

    try {
      if (!isLogin) {
        // Step 1: Sign up
        const signupRes = await fetch(`${apiUrl}/signup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: formData.username.trim(), password: formData.password }),
        });
        const signupData = await signupRes.json();
        if (!signupRes.ok) {
          throw new Error(signupData.detail || 'Signup failed.');
        }
      }

      // Step 2: Login (for both login and post-signup)
      const loginRes = await fetch(`${apiUrl}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: formData.username.trim(), password: formData.password }),
      });
      const loginData = await loginRes.json();
      if (!loginRes.ok) {
        throw new Error(loginData.detail || 'Login failed.');
      }

      if (!loginData.access_token) {
        throw new Error('No access token received.');
      }

      onLogin(loginData.access_token, formData.username.trim());
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setIsLogin(!isLogin);
    setError('');
    setSuccess('');
    setFormData({ username: '', password: '' });
    setConfirmPassword('');
  };

  return (
    <div className="auth-container">
      <div className="auth-box">
        <h1>&#x1F4DD; Notes App</h1>
        <h2>{isLogin ? 'Welcome Back!' : 'Create Account'}</h2>

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="input-group">
            <input
              type="text"
              placeholder="Username"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              autoComplete="username"
              required
            />
          </div>

          <div className="input-group">
            <input
              type="password"
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              autoComplete={isLogin ? 'current-password' : 'new-password'}
              required
            />
          </div>

          {!isLogin && (
            <div className="input-group">
              <input
                type="password"
                placeholder="Confirm Password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
          )}

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? 'Please wait...' : isLogin ? 'Sign In' : 'Sign Up'}
          </button>
        </form>

        <p className="auth-switch">
          {isLogin ? "Don't have an account? " : 'Already have an account? '}
          <button className="link-btn" onClick={switchMode} type="button">
            {isLogin ? 'Sign Up' : 'Sign In'}
          </button>
        </p>
      </div>
    </div>
  );
}

export default Auth;
