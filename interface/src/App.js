import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { Layout, ProtectedRoute } from './components/Layout';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Appointments from './pages/Appointments';
import Queue from './pages/Queue';
import Patients from './pages/Patients';
import PatientDetail from './pages/PatientDetail';
import OPDForm from './pages/OPDForm';
import Billing from './pages/Billing';
import Doctors from './pages/Doctors';
import Settings from './pages/Settings';
import Reports from './pages/Reports';
import AgentAnalytics from './pages/AgentAnalytics';

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Toaster position="top-right" />
          <Routes>
            <Route path="/login" element={<Login />} />
            
            {/* Protected Routes */}
            <Route path="/dashboard" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
            <Route path="/appointments" element={<ProtectedRoute><Layout><Appointments /></Layout></ProtectedRoute>} />
            <Route path="/queue" element={<ProtectedRoute><Layout><Queue /></Layout></ProtectedRoute>} />
            <Route path="/patients" element={<ProtectedRoute><Layout><Patients /></Layout></ProtectedRoute>} />
            <Route path="/patients/:id" element={<ProtectedRoute><Layout><PatientDetail /></Layout></ProtectedRoute>} />
            <Route path="/patients/:id/opd" element={<ProtectedRoute><Layout><OPDForm /></Layout></ProtectedRoute>} />
            <Route path="/billing" element={<ProtectedRoute><Layout><Billing /></Layout></ProtectedRoute>} />
            <Route path="/doctors" element={<ProtectedRoute><Layout><Doctors /></Layout></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><Layout><Settings /></Layout></ProtectedRoute>} />
            <Route path="/reports" element={<ProtectedRoute><Layout><Reports /></Layout></ProtectedRoute>} />
            <Route path="/ai-logs" element={<ProtectedRoute><Layout><AgentAnalytics /></Layout></ProtectedRoute>} />
            
            {/* Fallback */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
