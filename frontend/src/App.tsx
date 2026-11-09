import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import LiveOperations from './pages/LiveOperations';
import ThreatIntel from './pages/ThreatIntel';
import SystemHealth from './pages/SystemHealth';
import AuditViewer from './pages/AuditViewer';

// Routes intentionally avoid the API prefixes (/health, /audit, /live, /intel, /webhooks) so the
// backend can serve this SPA from the same origin.
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<LiveOperations />} />
          <Route path="threats" element={<ThreatIntel />} />
          <Route path="ledger" element={<AuditViewer />} />
          <Route path="integrations" element={<SystemHealth />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
