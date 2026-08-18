import { useState } from 'react';
import { API_BASE_URL } from "../config";

const initialFormState = {
  Time: '',
  Amount: '',
};
for (let i = 1; i <= 28; i++) {
  initialFormState[`V${i}`] = '';
}


function PredictionForm() {
  const [formData, setFormData] = useState(initialFormState);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false); // collapsed by default

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const loadSample = async (isFraud) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/sample-transaction?fraud=${isFraud}`);
      const data = await response.json();
      const stringified = {};
      for (const key in data) {
        stringified[key] = String(data[key]);
      }
      setFormData(stringified);
      setShowAdvanced(true); // auto-expand so you can see the loaded values
    } catch (err) {
      setError('Could not load sample transaction: ' + err.message);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);

    const payload = {};
    for (const key in formData) {
      payload[key] = parseFloat(formData[key]);
    }

    try {
      const response = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorBody = await response.json();
        throw new Error(errorBody.detail || `Request failed with status ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const vFeatures = Array.from({ length: 28 }, (_, i) => `V${i + 1}`);

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <h2>Fraud Detection — Transaction Check</h2>

        <div>
          <button type="button" onClick={() => loadSample(false)}>Load Legitimate Example</button>
          <button type="button" onClick={() => loadSample(true)}>Load Fraud Example</button>
        </div>

        <div>
          <label>Time (seconds since first transaction)</label>
          <input type="number" name="Time" value={formData.Time} onChange={handleChange} required />
        </div>

        <div>
          <label>Amount</label>
          <input type="number" name="Amount" value={formData.Amount} onChange={handleChange} step="0.01" required />
        </div>

        <button
          type="button"
          onClick={() => setShowAdvanced((prev) => !prev)}
          style={{ marginTop: '1rem' }}
        >
          {showAdvanced ? 'Hide' : 'Show'} Advanced Features (V1–V28)
        </button>

        {/* Only rendered when expanded -- a compact grid instead of 28 stacked rows */}
        {showAdvanced && (
          <div className="v-feature-grid">
            {vFeatures.map((featureName) => (
              <div key={featureName}>
                <label>{featureName}</label>
                <input
                  type="number"
                  name={featureName}
                  value={formData[featureName]}
                  onChange={handleChange}
                  step="any"
                  required
                />
              </div>
            ))}
          </div>
        )}

        <div>
          <button type="submit" disabled={loading}>
            {loading ? 'Checking...' : 'Check Transaction'}
          </button>
        </div>
      </form>

      {error && <p style={{ color: '#ff3131' }}>Error: {error}</p>}

      {result && (
        <div style={{ border: '1px solid #009938', padding: '1rem', marginTop: '1rem' }}>
          <h3>{result.message}</h3>
          <p>Fraud probability: {(result.fraud_probability * 100).toFixed(2)}%</p>
        </div>
      )}
    </div>
  );
}

export default PredictionForm;