import React from 'react';
import { TrendUp, TrendDown, CalendarCheck } from '@phosphor-icons/react';

export default function MarketVelocityTicker({ allPlayers = [], onInspectPlayer }) {
  // Rising and falling assets
  const risingAssets = [
    { web_name: 'Cherki', team: 'Man City', pos: 'MID', cost: 7.5, net_vel: 142050, trend: 'Rising Tonight', ratio: '124% of threshold' },
    { web_name: 'B.Fernandes', team: 'Man Utd', pos: 'MID', cost: 12.0, net_vel: 98400, trend: 'Rising Soon', ratio: '88% of threshold' },
    { web_name: 'Gabriel', team: 'Arsenal', pos: 'DEF', cost: 8.0, net_vel: 84200, trend: 'Rising Soon', ratio: '79% of threshold' },
    { web_name: 'Raya', team: 'Arsenal', pos: 'GK', cost: 6.0, net_vel: 76500, trend: 'Rising Soon', ratio: '76% of threshold' },
  ];

  const fallingAssets = [
    { web_name: 'Palmer', team: 'Chelsea', pos: 'MID', cost: 10.5, net_vel: -118300, trend: 'Dropping Tonight', ratio: '108% of threshold' },
    { web_name: 'Watkins', team: 'Aston Villa', pos: 'FWD', cost: 9.0, net_vel: -92400, trend: 'Dropping Soon', ratio: '84% of threshold' },
    { web_name: 'Trippier', team: 'Newcastle', pos: 'DEF', cost: 5.5, net_vel: -81200, trend: 'Dropping Soon', ratio: '78% of threshold' },
  ];

  const chips = [
    { name: 'Triple Captain (3XC)', target_gw: 'GW25 or GW34', value: '+14.2 pts gain', reason: 'Save for a prolific premium attacker (Haaland/Salah) during a Double Gameweek.' },
    { name: 'Bench Boost (BB)', target_gw: 'GW37', value: '+18.5 pts gain', reason: 'Deploy when your entire 15-man squad has two fixtures in the biggest double gameweek of the season.' },
    { name: 'Free Hit (FH)', target_gw: 'GW29', value: '+22.0 pts gain', reason: 'Navigate FA Cup clash weekends when only 8–10 clubs play, fielding a full XI without burning transfers.' },
    { name: 'First Wildcard (WC1)', target_gw: 'GW6 to GW8', value: '+9.4 pts per GW', reason: 'Capitalize on the major early-season fixture swing to load up on Arsenal, City, and Liverpool assets.' },
  ];

  // Helper to trigger inspection by matching asset name
  const handleInspect = (asset) => {
    if (!onInspectPlayer) return;
    const matched = allPlayers.find(
      p => (p.web_name || '').toLowerCase() === asset.web_name.toLowerCase()
    );
    if (matched) {
      onInspectPlayer(matched);
    } else {
      onInspectPlayer({
        web_name: asset.web_name,
        team: asset.team,
        position: asset.pos,
        cost: asset.cost,
        expected_points: 5.2
      });
    }
  };

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        {/* Rising Assets Radar */}
        <div className="sidebar-panel">
          <div className="panel-header">
            <span style={{ color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <TrendUp size={16} weight="bold" />
              Players Set to Rise in Price (+£0.1m)
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {risingAssets.map(p => (
              <div
                key={p.web_name}
                onClick={() => handleInspect(p)}
                style={{
                  background: 'var(--bg-surface-2)',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
                className="bench-item"
                title="Click to view player stats"
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span className={`player-position-pill ${p.pos}`}>{p.pos}</span>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{p.web_name}</span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>({p.team})</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                    £{p.cost.toFixed(1)}m · +{p.net_vel.toLocaleString()} net transfers
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span style={{ background: 'rgba(16, 185, 129, 0.2)', color: 'var(--accent-emerald)', fontSize: '11px', fontWeight: 700, padding: '2px 8px', borderRadius: 'var(--radius-xs)' }}>
                    {p.trend}
                  </span>
                  <div style={{ fontSize: '10px', color: 'var(--text-secondary)', marginTop: '3px' }}>
                    {p.ratio}
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
              <TrendDown size={16} weight="bold" />
              Players Set to Drop in Price (-£0.1m)
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {fallingAssets.map(p => (
              <div
                key={p.web_name}
                onClick={() => handleInspect(p)}
                style={{
                  background: 'var(--bg-surface-2)',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
                className="bench-item"
                title="Click to view player stats"
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span className={`player-position-pill ${p.pos}`}>{p.pos}</span>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{p.web_name}</span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>({p.team})</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                    £{p.cost.toFixed(1)}m · {p.net_vel.toLocaleString()} net transfers
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span style={{ background: 'rgba(239, 68, 68, 0.2)', color: 'var(--accent-crimson)', fontSize: '11px', fontWeight: 700, padding: '2px 8px', borderRadius: 'var(--radius-xs)' }}>
                    {p.trend}
                  </span>
                  <div style={{ fontSize: '10px', color: 'var(--text-secondary)', marginTop: '3px' }}>
                    {p.ratio}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Strategic Chip Guide */}
      <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <CalendarCheck size={18} weight="bold" />
        Chip Strategy Guide & Target Windows
      </h3>

      <div className="roadmap-grid">
        {chips.map(c => (
          <div key={c.name} className="roadmap-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>{c.name}</span>
              <span style={{ fontSize: '12px', color: 'var(--accent-amber)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{c.value}</span>
            </div>
            <div style={{ fontSize: '13px', color: 'var(--accent-emerald)', fontWeight: 700, marginBottom: '6px' }}>
              Recommended Target: {c.target_gw}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              {c.reason}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
