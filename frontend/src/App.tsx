import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet, useParams, useSearchParams } from 'react-router-dom';
import { LazyMotion, domAnimation } from 'framer-motion';
import AuthGuard from '@/components/layout/AuthGuard';
import PageLoader from '@/components/layout/PageLoader';
import ErrorBoundary from '@/components/layout/ErrorBoundary';
import { LanguageProvider } from '@/lib/i18n';
import ToastContainer from '@/components/layout/ToastContainer';

// Lazy-loaded page components for route-based code splitting
const LoginPage = lazy(() => import('@/pages/Login'));
const SignupPage = lazy(() => import('@/pages/Signup'));
const ResetPasswordPage = lazy(() => import('@/pages/ResetPassword'));
const DashboardPage = lazy(() => import('@/pages/Dashboard'));
const PatientsPage = lazy(() => import('@/pages/Patients'));
const PatientDetailPage = lazy(() => import('@/pages/PatientDetail'));
const ChatPage = lazy(() => import('@/pages/Chat'));
const TelemedicinePage = lazy(() => import('@/pages/Telemedicine'));
const PredictPage = lazy(() => import('@/pages/Predict'));
const UnifiedHubPage = lazy(() => import('@/pages/UnifiedHub'));
const DynamicPredictPage = lazy(() => import('@/pages/DynamicPredict'));
const InfrastructurePage = lazy(() => import('@/pages/Infrastructure'));
const CapacityPage = lazy(() => import('@/pages/Capacity'));
const AdminPage = lazy(() => import('@/pages/Admin'));
const ProfilePage = lazy(() => import('@/pages/Profile'));
const PricingPage = lazy(() => import('@/pages/Pricing'));
const AboutPage = lazy(() => import('@/pages/About'));
const AppRegistryPage = lazy(() => import('@/pages/AppRegistry'));
const FederatedLearningPage = lazy(() => import('@/pages/FederatedLearning'));
const ClinicalIntelligencePage = lazy(() => import('@/pages/ClinicalIntelligence'));
const CompanionPage = lazy(() => import('@/pages/Companion'));
const DataEngineeringPage = lazy(() => import('@/pages/DataEngineering'));
const TelemetryPage = lazy(() => import('@/pages/Telemetry'));

// Layout wrapper that applies authentication guards and TopNav template
function ProtectedLayout() {
  return (
    <AuthGuard>
      <Outlet />
    </AuthGuard>
  );
}

// Router parameters wrapper for Patient EMR page
function PatientDetailPageWrapper() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const intent = searchParams.get('intent') || undefined;

  return (
    <PatientDetailPage
      id={id || ''}
      intent={intent}
    />
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <LanguageProvider>
        <LazyMotion features={domAnimation} strict>
          <BrowserRouter>
            <Suspense fallback={<PageLoader />}>
              <Routes>
                {/* Public Routes */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/signup" element={<SignupPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />

                {/* Protected Dashboard & Operations Routes */}
                <Route element={<ProtectedLayout />}>
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/patients" element={<PatientsPage />} />
                  <Route path="/patients/:id" element={<PatientDetailPageWrapper />} />
                  <Route path="/chat" element={<ChatPage />} />
                  <Route path="/telemedicine" element={<TelemedicinePage />} />
                  <Route path="/predict" element={<PredictPage />} />
                  <Route path="/predict/unified" element={<UnifiedHubPage />} />
                  <Route path="/predict/:modelType" element={<DynamicPredictPage />} />
                  <Route path="/infrastructure" element={<InfrastructurePage />} />
                  <Route path="/capacity" element={<CapacityPage />} />
                  <Route path="/admin" element={<AdminPage />} />
                  <Route path="/profile" element={<ProfilePage />} />
                  <Route path="/pricing" element={<PricingPage />} />
                  <Route path="/about" element={<AboutPage />} />
                  <Route path="/apps" element={<AppRegistryPage />} />
                  <Route path="/federated" element={<FederatedLearningPage />} />
                  <Route path="/intelligence" element={<ClinicalIntelligencePage />} />
                  <Route path="/companion" element={<CompanionPage />} />
                  <Route path="/data-engineering" element={<DataEngineeringPage />} />
                  <Route path="/telemetry" element={<TelemetryPage />} />
                </Route>

                {/* Fallback redirects to Dashboard */}
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Suspense>
            <ToastContainer />
          </BrowserRouter>
        </LazyMotion>
      </LanguageProvider>
    </ErrorBoundary>
  );
}
