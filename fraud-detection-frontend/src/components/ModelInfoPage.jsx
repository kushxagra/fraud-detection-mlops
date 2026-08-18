import { useState, useEffect } from 'react';

const MODEL_INFO_URL = 'http://127.0.0.1:8000/model-info';
const RETRAIN_URL = 'http://127.0.0.1:8000/retrain';

function ModelInfoPage() {
  const [modelInfo, setModelInfo] = useState(null);
  const [error, setError] = useState(null);
  const [retraining, setRetraining] = useState(false);
  const [retrainMessage, setRetrainMessage] = useState(null);

  // Pulled out into its own function so we can call it both on page load
  // AND again after a successful retrain, to refresh the displayed info.
  const fetchModelInfo = async () => {
    try {
      const response = await fetch(MODEL_INFO_URL);
      if (!response.ok) throw new Error('Failed to fetch model info');
      setModelInfo(await response.json());
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    fetchModelInfo();
  }, []);

  const handleRetrain = async () => {
    setRetraining(true);
    setRetrainMessage(null);
    setError(null);

    try {
      const response = await fetch(RETRAIN_URL, { method: 'POST' });
      if (!response.ok) {
        const errorBody = await response.json();
        throw new Error(errorBody.detail || 'Retrain failed');
      }
      const data = await response.json();
      setRetrainMessage(data.message);

      // Refresh the displayed model info now that a new version is active
      await fetchModelInfo();
    } catch (err) {
      setError(err.message);
    } finally {
      setRetraining(false);
    }
  };

  if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;
  if (!modelInfo) return <p>Loading model info...</p>;

  return (
    <div>
      <h2>Active Model</h2>
      <p>Version: {modelInfo.model_version}</p>
      <p>Trained at: {modelInfo.metadata.trained_at}</p>
      <p>Accuracy: {modelInfo.metadata.baseline_metrics?.accuracy}</p>
      <p>Fraud precision: {modelInfo.metadata.baseline_metrics?.fraud_precision}</p>
      <p>Fraud recall: {modelInfo.metadata.baseline_metrics?.fraud_recall}</p>

      <button onClick={handleRetrain} disabled={retraining}>
        {retraining ? 'Retraining... this may take a minute' : 'Retrain Model'}
      </button>

      {retrainMessage && <p style={{ color: 'green' }}>{retrainMessage}</p>}
    </div>
  );
}

export default ModelInfoPage;