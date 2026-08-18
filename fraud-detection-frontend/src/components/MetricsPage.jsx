import { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';

const METRICS_URL = `${API_BASE_URL}/metrics`;

function MetricsPage() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(METRICS_URL);
        if (!response.ok) throw new Error('Failed to fetch metrics');
        setMetrics(await response.json());
      } catch (err) {
        setError(err.message);
      }
    };
    fetchData();
  }, []);

  if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;
  if (!metrics) return <p>Loading metrics...</p>;

  return (
    <div>
      <h2>Prediction Stats</h2>
      <p>Total predictions: {metrics.total_predictions}</p>
      <p>Fraud detected: {metrics.fraud_detected}</p>
      <p>Legitimate: {metrics.legitimate}</p>
      <p>Fraud rate: {metrics.fraud_rate}%</p>
      <p>Last prediction: {metrics.last_prediction || 'N/A'}</p>
    </div>
  );
}

export default MetricsPage;