import { useState, useEffect } from 'react';

const RECENT_URL = 'http://127.0.0.1:8000/predictions/recent?limit=20';

function PredictionHistory() {
  const [predictions, setPredictions] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(RECENT_URL);
        if (!response.ok) {
          throw new Error('Failed to fetch prediction history');
        }
        const data = await response.json();
        setPredictions(data.predictions);
      } catch (err) {
        setError(err.message);
      }
    };

    fetchData();
  }, []);

  if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;
  if (!predictions) return <p>Loading history...</p>;

  return (
    <div>
      <h3>Recent Predictions</h3>
      <table border="1" cellPadding="6" style={{ borderCollapse: 'collapse', width: '100%' }}>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Amount</th>
            <th>Result</th>
            <th>Fraud Probability</th>
            <th>Model Version</th>
          </tr>
        </thead>
        <tbody>
          {predictions.map((p, index) => (
            <tr key={index}>
              <td>{p.timestamp}</td>
              <td>{p.amount}</td>
              <td style={{ color: p.is_fraud ? 'red' : 'green' }}>
                {p.is_fraud ? 'Fraud' : 'Legitimate'}
              </td>
              <td>{(p.fraud_probability * 100).toFixed(2)}%</td>
              <td>{p.model_version}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default PredictionHistory;