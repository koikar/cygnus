import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts';
import useAppStore from '../store/useAppStore.js';

const MODE_COLORS = {
  habit: '#2d8cf0',
  system2: '#ff8c00',
  reflex: '#00d68f',
};

const MODE_LABELS = {
  habit: 'Habit',
  system2: 'AI Recovery',
  reflex: 'Reflex',
};

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius)', padding: '10px 14px', fontSize: 11,
    }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>Episode {d.episode}</div>
      <div style={{ color: 'var(--text-secondary)' }}>Cost: <span style={{ color: MODE_COLORS[d.mode], fontWeight: 600 }}>{d.cost} steps</span></div>
      <div style={{ color: 'var(--text-secondary)' }}>Mode: <span style={{ color: MODE_COLORS[d.mode] }}>{MODE_LABELS[d.mode]}</span></div>
      {d.escalated && <div style={{ color: '#ff8c00', marginTop: 2 }}>⚡ Black-swan detected</div>}
    </div>
  );
};

// Pre-populated data so the chart shows even before demo runs
const SEED_HISTORY = [
  { episode: 1, cost: 4, mode: 'habit', success: true, escalated: false },
];

export default function AntifragilityChart() {
  const episodeHistory = useAppStore(s => s.episodeHistory);
  const publicMode = useAppStore(s => s.publicMode);

  const data = episodeHistory.length > 0 ? episodeHistory : SEED_HISTORY;

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title-dot" style={{ background: 'var(--accent-orange)' }} />
        {publicMode ? 'HOW MUCH FASTER OVER TIME' : 'EPISODE COST — ANTIFRAGILITY CHART'}
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 16, flexWrap: 'wrap' }}>
        {Object.entries(MODE_COLORS).map(([mode, color]) => (
          <div key={mode} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: 'var(--text-secondary)' }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: color }} />
            {MODE_LABELS[mode]}
          </div>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis
            dataKey="episode"
            tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            label={{ value: 'Episode', fill: 'var(--text-muted)', fontSize: 10, position: 'insideBottom', offset: -2 }}
          />
          <YAxis
            tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            domain={[0, 10]}
            label={{ value: 'Cost', fill: 'var(--text-muted)', fontSize: 10, angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
          <ReferenceLine y={4} stroke="rgba(0,214,143,0.3)" strokeDasharray="4 4" label={{ value: 'Reflex target', fill: 'var(--accent-green)', fontSize: 9, position: 'right' }} />
          <Bar dataKey="cost" radius={[4, 4, 0, 0]} maxBarSize={48}>
            {data.map((entry, i) => (
              <Cell key={i} fill={MODE_COLORS[entry.mode] || '#2d8cf0'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {data.length > 0 && (
        <div style={{ marginTop: 12, fontSize: 10, color: 'var(--text-muted)', textAlign: 'center' }}>
          {publicMode
            ? 'Green bar = robot used its memory shortcut — much faster!'
            : 'Reflex episodes (green) cost half compared to system2 recovery episodes (orange)'
          }
        </div>
      )}
    </div>
  );
}
