import React, { useState, useEffect } from 'react';
import { listRFPs } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

function StatCard({ icon, label, value, color }) {
  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '20px 24px',
      border: '1px solid #eee',
      display: 'flex',
      alignItems: 'center',
      gap: '16px'
    }}>
      <div style={{
        width: '48px',
        height: '48px',
        borderRadius: '12px',
        background: color + '18',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '22px'
      }}>{icon}</div>
      <div>
        <div style={{ fontSize: '28px', fontWeight: '700', color: '#1a1a2e' }}>{value}</div>
        <div style={{ fontSize: '13px', color: '#888' }}>{label}</div>
      </div>
    </div>
  );
}

function Dashboard({ user, onNewRFP }) {
  const [rfps, setRfps] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await listRFPs();
        const myRfps = res.data.rfps.filter(r => r.user_id === user.id);
        setRfps(myRfps);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [user]);

  const total = rfps.length;
  const approved = rfps.filter(r => r.status === 'approved').length;
  const processing = rfps.filter(r => r.status === 'processing' || r.status === 'uploaded').length;
  const awaiting = rfps.filter(r => r.status === 'awaiting_approval').length;

  const pieData = [
    { name: 'Approved', value: approved || 0, color: '#2e7d32' },
    { name: 'Awaiting', value: awaiting || 0, color: '#f59e0b' },
    { name: 'Processing', value: processing || 0, color: '#1976d2' },
  ].filter(d => d.value > 0);

  // Last 7 days activity
  const last7Days = Array.from({ length: 7 }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - (6 - i));
    const label = date.toLocaleDateString('en-US', { weekday: 'short' });
    const count = rfps.filter(r => {
      const rfpDate = new Date(r.created_at);
      return rfpDate.toDateString() === date.toDateString();
    }).length;
    return { label, count };
  });

  const recentRfps = [...rfps].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 5);

  const statusColor = (status) => {
    if (status === 'awaiting_approval') return '#f59e0b';
    if (status === 'approved') return '#2e7d32';
    if (status === 'processing') return '#1976d2';
    if (status === 'error') return '#cc0000';
    return '#888';
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: '0 0 4px', fontSize: '26px', color: '#1a1a2e' }}>
            Welcome back, {user.user_metadata?.full_name?.split(' ')[0] || 'there'} 👋
          </h1>
          <p style={{ margin: 0, color: '#888', fontSize: '14px' }}>
            Here's an overview of your RFP activity
          </p>
        </div>
        <button
          onClick={onNewRFP}
          style={{
            background: '#1a1a2e',
            color: 'white',
            border: 'none',
            borderRadius: '10px',
            padding: '12px 24px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          + New RFP
        </button>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '32px' }}>
        <StatCard icon="📄" label="Total RFPs" value={total} color="#1976d2" />
        <StatCard icon="✅" label="Approved" value={approved} color="#2e7d32" />
        <StatCard icon="⏳" label="Awaiting Review" value={awaiting} color="#f59e0b" />
        <StatCard icon="⚙️" label="Processing" value={processing} color="#9c27b0" />
      </div>

      {/* Charts row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '32px' }}>
        {/* Bar chart */}
        <div style={{ background: 'white', borderRadius: '12px', padding: '24px', border: '1px solid #eee' }}>
          <h3 style={{ margin: '0 0 20px', fontSize: '15px', color: '#1a1a2e' }}>RFPs this week</h3>
          {loading ? (
            <div style={{ height: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888' }}>Loading...</div>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={last7Days}>
                <XAxis dataKey="label" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#1a1a2e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Pie chart */}
        <div style={{ background: 'white', borderRadius: '12px', padding: '24px', border: '1px solid #eee' }}>
          <h3 style={{ margin: '0 0 20px', fontSize: '15px', color: '#1a1a2e' }}>Status breakdown</h3>
          {pieData.length === 0 ? (
            <div style={{ height: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888', fontSize: '14px' }}>
              No data yet
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
              <PieChart width={160} height={160}>
                <Pie data={pieData} cx={75} cy={75} innerRadius={45} outerRadius={70} dataKey="value">
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
              <div>
                {pieData.map((entry, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: entry.color }} />
                    <span style={{ fontSize: '13px', color: '#555' }}>{entry.name}: <strong>{entry.value}</strong></span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recent RFPs */}
      <div style={{ background: 'white', borderRadius: '12px', padding: '24px', border: '1px solid #eee' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ margin: 0, fontSize: '15px', color: '#1a1a2e' }}>Recent RFPs</h3>
        </div>
        {loading ? (
          <p style={{ color: '#888', textAlign: 'center', padding: '24px' }}>Loading...</p>
        ) : recentRfps.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px', color: '#888' }}>
            <div style={{ fontSize: '32px', marginBottom: '8px' }}>📭</div>
            <p>No RFPs yet. Upload your first one!</p>
            <button
              onClick={onNewRFP}
              style={{
                background: '#1a1a2e', color: 'white', border: 'none',
                borderRadius: '8px', padding: '10px 20px', cursor: 'pointer', fontSize: '14px'
              }}
            >
              Upload RFP
            </button>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #eee' }}>
                {['Filename', 'Status', 'Created', 'Progress'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '8px 12px', fontSize: '12px', color: '#888', fontWeight: '600', textTransform: 'uppercase' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {recentRfps.map(rfp => {
                const progress = rfp.current_progress || {};
                const done = Object.values(progress).filter(v => v === 'completed').length;
                const pct = Math.round((done / 4) * 100);
                return (
                  <tr key={rfp.id} style={{ borderBottom: '1px solid #f5f5f5' }}>
                    <td style={{ padding: '12px', fontSize: '14px', color: '#1a1a2e' }}>
                      📄 {rfp.filename || 'Unnamed'}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span style={{
                        background: statusColor(rfp.status) + '18',
                        color: statusColor(rfp.status),
                        padding: '3px 10px',
                        borderRadius: '99px',
                        fontSize: '12px',
                        fontWeight: '500'
                      }}>
                        {rfp.status}
                      </span>
                    </td>
                    <td style={{ padding: '12px', fontSize: '13px', color: '#888' }}>
                      {new Date(rfp.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ flex: 1, height: '6px', background: '#f0f0f0', borderRadius: '3px' }}>
                          <div style={{ width: `${pct}%`, height: '100%', background: '#1a1a2e', borderRadius: '3px', transition: 'width 0.3s' }} />
                        </div>
                        <span style={{ fontSize: '12px', color: '#888', minWidth: '30px' }}>{pct}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default Dashboard;