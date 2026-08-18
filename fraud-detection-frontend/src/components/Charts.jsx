import { useState, useEffect } from 'react';
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid
} from 'recharts';
import { API_BASE_URL } from "../config";


const METRICS_URL = `${API_BASE_URL}/metrics`;
const RECENT_URL = `${API_BASE_URL}/predictions/recent?limit=20`;


const COLORS = ['#009938', '#ff3131']; // validated: legitimate (good) / fraud (critical)
function Charts() {
  const [pieData, setPieData] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [metricsRes, recentRes] = await Promise.all([
          fetch(METRICS_URL),
          fetch(RECENT_URL),
        ]);

        if (!metricsRes.ok || !recentRes.ok) {
          throw new Error('Failed to fetch chart data');
        }

        const metrics = await metricsRes.json();
        const recent = await recentRes.json();

        setPieData([
          { name: 'Legitimate', value: metrics.legitimate },
          { name: 'Fraud', value: metrics.fraud_detected },
        ]);

        // Recharts reads a line chart left-to-right as chronological, but
        // our API returns newest-first -- so we reverse it here.
        const chronological = [...recent.predictions].reverse().map((p, index) => ({
          index: index + 1,
          probability: p.fraud_probability,
        }));
        setHistoryData(chronological);
      } catch (err) {
        setError(err.message);
      }
    };

    fetchData();
  }, []);

  if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;
  if (!pieData || !historyData) return <p>Loading charts...</p>;

  return (
    <div>
      <h3>Fraud vs Legitimate</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={100} label>
            {pieData.map((entry, index) => (
              <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>

      <h3>Fraud Probability — Recent Predictions</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={historyData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="index" label={{ value: 'Prediction #', position: 'insideBottom', offset: -5 }} />
          <YAxis domain={[0, 1]} />
          <Tooltip />
          <Line type="monotone" dataKey="probability" stroke="#8884d8" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default Charts;