import React, { useState, useEffect } from 'react';
import { supabase } from './services/supabase';
import Login from './components/Login';
import Upload from './components/Upload';
import Pipeline from './components/Pipeline';
import Approval from './components/Approval';
import History from './components/History';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [rfpId, setRfpId] = useState(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setAuthLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setUser(null);
    setCurrentPage('dashboard');
    setRfpId(null);
  };

  const handleUploadSuccess = (id) => {
    setRfpId(id);
    setCurrentPage('pipeline');
  };

  const handleApprove = () => setCurrentPage('approval');
  
  const handleReset = () => {
    setRfpId(null);
    setCurrentPage('dashboard');
  };

  if (authLoading) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8f9fa' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '32px', marginBottom: '12px' }}>📋</div>
        <p style={{ color: '#888' }}>Loading CORE-RFP...</p>
      </div>
    </div>
  );

  if (!user) return <Login />;

  const navItems = [
    { key: 'dashboard', icon: '⬛', label: 'Dashboard' },
    { key: 'upload', icon: '📤', label: 'New RFP' },
    { key: 'history', icon: '📁', label: 'My RFPs' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f8f9fa' }}>
      {/* Sidebar */}
      <div style={{
        width: '240px',
        background: '#1a1a2e',
        color: 'white',
        display: 'flex',
        flexDirection: 'column',
        position: 'fixed',
        height: '100vh',
        zIndex: 100
      }}>
        {/* Logo */}
        <div style={{ padding: '24px 20px', borderBottom: '1px solid #2d2d44' }}>
          <div style={{ fontSize: '22px', fontWeight: '700', letterSpacing: '-0.5px' }}>
            📋 CORE-RFP
          </div>
          <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>
            AI Proposal System
          </div>
        </div>

        {/* Nav */}
        <nav style={{ padding: '16px 12px', flex: 1 }}>
          {navItems.map(({ key, icon, label }) => (
            <button
              key={key}
              onClick={() => setCurrentPage(key)}
              style={{
                width: '100%',
                padding: '10px 12px',
                marginBottom: '4px',
                border: 'none',
                borderRadius: '8px',
                background: currentPage === key ? '#2d2d5e' : 'transparent',
                color: currentPage === key ? 'white' : '#aaa',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                fontSize: '14px',
                fontWeight: currentPage === key ? '600' : '400',
                textAlign: 'left',
                transition: 'all 0.15s'
              }}
            >
              <span>{icon}</span>
              {label}
            </button>
          ))}
        </nav>

        {/* User */}
        <div style={{ padding: '16px', borderTop: '1px solid #2d2d44' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <img
              src={user.user_metadata?.avatar_url}
              alt="avatar"
              style={{ width: '32px', height: '32px', borderRadius: '50%' }}
              onError={e => e.target.style.display = 'none'}
            />
            <div>
              <div style={{ fontSize: '13px', fontWeight: '500', color: 'white' }}>
                {user.user_metadata?.full_name?.split(' ')[0] || 'User'}
              </div>
              <div style={{ fontSize: '11px', color: '#888', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '140px' }}>
                {user.email}
              </div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #2d2d44',
              borderRadius: '6px',
              background: 'transparent',
              color: '#888',
              cursor: 'pointer',
              fontSize: '13px'
            }}
          >
            Sign out
          </button>
        </div>
      </div>

      {/* Main content */}
      <div style={{ marginLeft: '240px', flex: 1, padding: '32px' }}>
        {currentPage === 'dashboard' && (
          <Dashboard user={user} onNewRFP={() => setCurrentPage('upload')} />
        )}
        {currentPage === 'upload' && (
          <Upload onSuccess={handleUploadSuccess} user={user} />
        )}
        {currentPage === 'pipeline' && (
          <Pipeline rfpId={rfpId} onApprove={handleApprove} />
        )}
        {currentPage === 'approval' && (
          <Approval rfpId={rfpId} onReset={handleReset} />
        )}
        {currentPage === 'history' && (
          <History user={user} onSelect={(id) => {
            setRfpId(id);
            setCurrentPage('approval');
          }} />
        )}
      </div>
    </div>
  );
}

export default App;