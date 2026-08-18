import { useState, useEffect } from 'react';
import Charts from './Charts';
import PredictionHistory from './PredictionHistory';


const METRICS_URL = 'http://127.0.0.1:8000/metrics';
const MODEL_INFO_URL = 'http://127.0.0.1:8000/model-info';

function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [error, setError] = useState(null);

  // useEffect with an empty [] dependency array runs exactly once, right
  // after this component first appears on screen -- this is how we fetch
  // data "on page load" instead of waiting for a button click.
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Promise.all runs both fetches at the same time instead of
        // waiting for one to finish before starting the other.
        const [metricsRes, modelInfoRes] = await Promise.all([
          fetch(METRICS_URL),
          fetch(MODEL_INFO_URL),
        ]);

        if (!metricsRes.ok || !modelInfoRes.ok) {
          throw new Error('Failed to fetch dashboard data');
        }

        setMetrics(await metricsRes.json());
        setModelInfo(await modelInfoRes.json());
      } catch (err) {
        setError(err.message);
      }
    };

    fetchData();
  }, []);

  if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;
  if (!metrics || !modelInfo) return <p>Loading dashboard...</p>;

  return (
    <div>
      <h2>Model Dashboard</h2>

      <section>
        <h3>Prediction Stats</h3>
        <p>Total predictions: {metrics.total_predictions}</p>
        <p>Fraud detected: {metrics.fraud_detected}</p>
        <p>Legitimate: {metrics.legitimate}</p>
        <p>Fraud rate: {metrics.fraud_rate}%</p>
        <p>Last prediction: {metrics.last_prediction || 'N/A'}</p>
      </section>

      <section>
        <h3>Active Model</h3>
        <p>Version: {modelInfo.active_version}</p>
        <p>Trained at: {modelInfo.metadata.trained_at}</p>
        {/* ?. means "only try to read this if baseline_metrics actually exists" --
            avoids a crash if an older model version has no metrics recorded */}
        <p>Accuracy: {modelInfo.metadata.baseline_metrics?.accuracy}</p>
        <p>Fraud precision: {modelInfo.metadata.baseline_metrics?.fraud_precision}</p>
        <p>Fraud recall: {modelInfo.metadata.baseline_metrics?.fraud_recall}</p>
      </section>
      <Charts />
      <PredictionHistory />
    </div>
  );
}

export default Dashboard;