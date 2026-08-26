import React from 'react';
import { TrendUp, TrendDown, CalendarCheck, Gauge } from '@phosphor-icons/react';

export default function MarketVelocityTicker({ allPlayers = [], onInspectPlayer }) {
  // Rising and falling assets with numeric progress (0-100+)
  const risingAssets = [
    { web_name: 'Cherki', team: 'Man City', pos: 'MID', cost: 7.5, net_vel: 142050, trend: 'Rising Tonight', ratio: '124% of threshold', progress: 124 },
    { web_name: 'B.Fernandes', team: 'Man Utd', pos: 'MID', cost: 12.0, net_vel: 98400, trend: 'Rising Soon', ratio: '88% of threshold', progress: 88 },
    { web_name: 'Gabriel', team: 'Arsenal', pos: 'DEF', cost: 8.0, net_vel: 84200, trend: 'Rising Soon', ratio: '79% of threshold', progress: 79 },
    { web_name: 'Raya', team: 'Arsenal', pos: 'GK', cost: 6.0, net_vel: 76500, trend: 'Rising Soon', ratio: '76% of threshold', progress: 76 },
  ];

  const fallingAssets = [
    { web_name: 'Palmer', team: 'Chelsea', pos: 'MID', cost: 10.5, net_vel: -118300, trend: 'Dropping Tonight', ratio: '108% of threshold', progress: 108 },
    { web_name: 'Watkins', team: 'Aston Villa', pos: 'FWD', cost: 9.0, net_vel: -92400, trend: 'Dropping Soon', ratio: '84% of threshold', progress: 84 },
    { web_name: 'Trippier', team: 'Newcastle', pos: 'DEF', cost: 5.5, net_vel: -81200, trend: 'Dropping Soon', ratio: '78% of threshold', progress: 78 },
  ];

  const chips = [
    { name: 'Triple Captain (3XC)', target_gw: 'GW25 or GW34', value: '+14.2 pts gain', reason: 'Deploy on a prolific premium attacker (Haaland/Salah) during a Double Gameweek.' },
    { name: 'Bench Boost (BB)', target_gw: 'GW37', value: '+18.5 pts gain', reason: 'Deploy when your entire 15-man squad has two fixtures in the season\'s largest double gameweek.' },
    { name: 'Free Hit (FH)', target_gw: 'GW29', value: '+22.0 pts gain', reason: 'Navigate blank FA Cup weekends when only 8–10 clubs play, fielding a full XI without burning transfers.' },
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
    <div className="view-fluid">
      <div className="market-panels-grid">
        {/* Rising Assets Radar */}
        <div className="sidebar-panel">
          <div className="panel-header">
            <span className="market-section-title rising">
              <TrendUp size={16} weight="bold" />
              <span>Players Set to Rise in Price (+£0.1m)</span>
            </span>
          </div>

          <div className="market-asset-list">
            {risingAssets.map(p => (
              <div
                key={p.web_name}
                onClick={() => handleInspect(p)}
                className="market-asset-row"
                title="Click to inspect player DNA"
              >
                <div className="asset-main-info">
                  <div className="market-asset-identity">
                    <span className={`player-pos-tag ${p.pos}`}>{p.pos}</span>
                    <span className="asset-player-name">{p.web_name}</span>
                    <span className="asset-team-name font-mono">({p.team})</span>
                  </div>
                  <div className="market-asset-meta font-mono">
                    £{p.cost.toFixed(1)}m · +{p.net_vel.toLocaleString()} net transfers
                  </div>
                  {/* Thermometer Progress Bar */}
                  <div className="velocity-thermometer-track">
                    <div
                      className={`velocity-thermometer-fill ${p.progress >= 100 ? 'saturated' : ''}`}
                      style={{ width: `${Math.min(100, p.progress)}%` }}
                    />
                  </div>
                </div>
                <div className="market-asset-trend">
                  <span className="market-trend-badge rising">{p.trend}</span>
                  <div className="market-trend-ratio font-mono">{p.ratio}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Falling Assets Radar */}
        <div className="sidebar-panel">
          <div className="panel-header">
            <span className="market-section-title falling">
              <TrendDown size={16} weight="bold" />
              <span>Players Set to Drop in Price (-£0.1m)</span>
            </span>
          </div>

          <div className="market-asset-list">
            {fallingAssets.map(p => (
              <div
                key={p.web_name}
                onClick={() => handleInspect(p)}
                className="market-asset-row"
                title="Click to inspect player DNA"
              >
                <div className="asset-main-info">
                  <div className="market-asset-identity">
                    <span className={`player-pos-tag ${p.pos}`}>{p.pos}</span>
                    <span className="asset-player-name">{p.web_name}</span>
                    <span className="asset-team-name font-mono">({p.team})</span>
                  </div>
                  <div className="market-asset-meta font-mono">
                    £{p.cost.toFixed(1)}m · {p.net_vel.toLocaleString()} net transfers
                  </div>
                  {/* Thermometer Progress Bar */}
                  <div className="velocity-thermometer-track">
                    <div
                      className={`velocity-thermometer-fill falling ${p.progress >= 100 ? 'saturated-falling' : ''}`}
                      style={{ width: `${Math.min(100, p.progress)}%` }}
                    />
                  </div>
                </div>
                <div className="market-asset-trend">
                  <span className="market-trend-badge falling">{p.trend}</span>
                  <div className="market-trend-ratio font-mono">{p.ratio}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Season Chip Optimization Guide */}
      <div className="chip-guide-panel">
        <div className="panel-header">
          <span className="market-section-title">
            <CalendarCheck size={16} weight="bold" />
            <span>Season Chip Strategy & Double Gameweek Roadmap</span>
          </span>
        </div>

        <div className="chip-guide-grid">
          {chips.map(chip => (
            <div key={chip.name} className="chip-guide-card">
              <div className="chip-guide-header">
                <span className="chip-guide-title font-mono">{chip.name}</span>
                <span className="chip-guide-gain font-mono">{chip.value}</span>
              </div>
              <div className="chip-guide-target font-mono">Recommended Target: {chip.target_gw}</div>
              <div className="chip-guide-reason">{chip.reason}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
