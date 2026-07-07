import React, { useState } from 'react';
import { supabase } from '../services/supabase';

function Login() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGoogleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: 'http://localhost:3000'
        }
      });
      if (error) setError(error.message);
    } catch (err) {
      setError('Login failed. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#f5f5f5',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '16px',
        padding: '48px',
        width: '400px',
        textAlign: 'center',
        boxShadow: '0 4px 24px rgba(0,0,0,0.08)'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📋</div>
        <h1 style={{ margin: '0 0 8px', fontSize: '28px', color: '#1a1a2e' }}>CORE-RFP</h1>
        <p style={{ color: '#888', marginBottom: '40px', fontSize: '15px' }}>
          AI-Powered Proposal Generation System
        </p>

        {error && (
          <div style={{
            background: '#fff0f0',
            border: '1px solid #ffcccc',
            borderRadius: '8px',
            padding: '12px',
            color: '#cc0000',
            marginBottom: '16px',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}

        <button
          onClick={handleGoogleLogin}
          disabled={loading}
          style={{
            width: '100%',
            padding: '14px',
            border: '1px solid #ddd',
            borderRadius: '10px',
            background: loading ? '#f5f5f5' : 'white',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            fontSize: '15px',
            fontWeight: '500',
            color: '#333'
          }}
        >
          <img
            src="https://www.google.com/favicon.ico"
            alt="Google"
            width="20"
            height="20"
          />
          {loading ? 'Redirecting...' : 'Continue with Google'}
        </button>

        <p style={{ color: '#bbb', fontSize: '12px', marginTop: '32px' }}>
          Your RFPs are private and only visible to you
        </p>
      </div>
    </div>
  );
}

export default Login;