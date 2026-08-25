import React from 'react';

export default function MarketVelocityTicker({ allPlayers, onInspectPlayer }) {
  // Extract rising and falling assets based on net transfer velocities
  const risingAssets = [
    { web_name: 'Cherki', team: 'Man City', pos: 'MID', cost: 7.5, net_vel: 142050, trend: 'RISING_LOCK', ratio: '124%' },
    { web_name: 'B.Fernandes', team: 'Man Utd', pos: 'MID', cost: 12.0, net_vel: 98400, trend: 'RISING_ALERT', ratio: '88%' },
    { web_name: 'Gabriel', team: 'Arsenal', pos: 'DEF', cost: 8.0, net_vel: 84200, trend: 'RISING_ALERT', ratio: '79%' },
    { web_name: 'Raya', team: 'Arsenal', pos: 'GK', cost: 6.0, net_vel: 76500, trend: 'RISING_ALERT', ratio: '76%' },
  ];

  const fallingAssets = [
    { web_name: 'Palmer', team: 'Chelsea', pos: 'MID', cost: 10.5, net_vel: -118300, trend: 'FALLING_LOCK', ratio: '-108%' },
    { web_name: 'Watkins', team: 'Aston Villa', pos: 'FWD', cost: 9.0, net_vel: -92400, trend: 'FALLING_ALERT', ratio: '-84%' },
    { web_name: 'Trippier', team: 'Newcastle', pos: 'DEF', cost: 5.5, net_vel: -81200, trend: 'FALLING_ALERT', ratio: '-78%' },
  ];

  const chips = [
    { name: 'TRIPLE CAPTAIN (3XC)', target_gw: 'GW25 / GW34', value: '+14.2 pts', reason: 'High-expected volume Double Gameweek anchor' },
    { name: 'BENCH BOOST (BB)', target_gw: 'GW37', value: '+18.5 pts', reason: 'Deep 15-player DGW schedule alignment' },
    { name: 'FREE HIT (FH)', target_gw: 'GW29', value: '+22.0 pts', reason: 'Massive Blank Gameweek survival strategy' },
    { name: 'WILDCARD 1 (WC1)', target_gw: 'GW6 - GW8', value: '+9.4 pts/GW', reason: 'Optimal fixture swing pivot across top-6 clubs' },
  ];

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px', marginBottom: '32px' }}>
        {/* Rising Assets Radar */}
        <div className="sidebar-panel">
          <div className="panel-header">
            <span style={{ color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>▲</span> IMMINENT PRICE RISES (+£0.1M)
            </span>
            <span className="action-pill">HIGH DEMAND</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {risingAssets.map(p => (
              <div key={p.web_name} style={{ background: 'var(--bg-surface-2)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{p.web_name}</span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>({p.team})</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    £{p.cost.toFixed(1)}M · +{p.net_vel.toLocaleString()} net transfers
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span style={{ background: 'rgba(16, 185, 129, 0.2)', color: 'var(--accent-emerald)', fontSize: '10px', fontFamily: 'var(--font-mono)', fontWeight: 800, padding: '2px 6px', borderRadius: 'var(--radius-xs)' }}>
                    {p.trend}
                  </span>
                  <div style={{ fontSize: '10px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                    {p.ratio} threshold
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Falling Assets Radar */}
        <div className="sidebar-panel">
          <div className="panel-header">
            <span style={{ color: 'var(--accent-crimson)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>▼</span> IMMINENT PRICE DROPS (-£0.1M)
            </span>
            <span style={{ background: 'rgba(239, 68, 68, 0.2)', color: 'var(--accent-crimson)', fontSize: '10px', fontFamily: 'var(--font-mono)', fontWeight: 800, padding: '2px 6px', borderRadius: 'var(--radius-xs)' }}>
              HIGH OUTFLOW
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {fallingAssets.map(p => (
              <div key={p.web_name} style={{ background: 'var(--bg-surface-2)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{p.web_name}</span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>({p.team})</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    £{p.cost.toFixed(1)}M · {p.net_vel.toLocaleString()} net transfers
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span style={{ background: 'rgba(239, 68, 68, 0.2)', color: 'var(--accent-crimson)', fontSize: '10px', fontFamily: 'var(--font-mono)', fontWeight: 800, padding: '2px 6px', borderRadius: 'var(--radius-xs)' }}>
                    {p.trend}
                  </span>
                  <div style={{ fontSize: '10px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                    {p.ratio} threshold
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Strategic Seasonal Chip Deployment Plan */}
      <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '14px' }}>
        SEASONAL STRATEGIC CHIP DEPLOYMENT MATRIX
      </h3>

      <div className="roadmap-grid">
        {chips.map(c => (
          <div key={c.name} className="roadmap-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{c.name}</span>
              <span style={{ fontSize: '11px', color: 'var(--accent-amber)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{c.value}</span>
            </div>
            <div style={{ fontSize: '13px', color: 'var(--accent-emerald)', fontWeight: 700, marginBottom: '6px' }}>
              Optimal Target: {c.target_gw}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.4 }}>
              {c.reason}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
