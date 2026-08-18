import { useState } from 'react';
import PredictionForm from './components/PredictionForm';
import MetricsPage from './components/MetricsPage';
import Charts from './components/Charts';
import PredictionHistory from './components/PredictionHistory';
import ModelInfoPage from './components/ModelInfoPage';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('predict');

  return (
    <div className="App">
      <nav>
        <button onClick={() => setActiveTab('predict')}>Predict</button>
        <button onClick={() => setActiveTab('metrics')}>Metrics</button>
        <button onClick={() => setActiveTab('charts')}>Charts</button>
        <button onClick={() => setActiveTab('history')}>History</button>
        <button onClick={() => setActiveTab('model-info')}>Model Info</button>
      </nav>

      {activeTab === 'predict' && <PredictionForm />}
      {activeTab === 'metrics' && <MetricsPage />}
      {activeTab === 'charts' && <Charts />}
      {activeTab === 'history' && <PredictionHistory />}
      {activeTab === 'model-info' && <ModelInfoPage />}
    </div>
  );
}

export default App;