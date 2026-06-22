import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet, useParams, useSearchParams } from 'react-router-dom';
import AuthGuard from '@/components/layout/AuthGuard';
import PageLoader from '@/components/layout/PageLoader';
import ErrorBoundary from '@/components/layout/ErrorBoundary';
import { LanguageProvider } from '@/lib/i18n';

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
const DiabetesPredictPage = lazy(() => import('@/pages/DiabetesPredict'));
const HeartPredictPage = lazy(() => import('@/pages/HeartPredict'));
const KidneyPredictPage = lazy(() => import('@/pages/KidneyPredict'));
const LiverPredictPage = lazy(() => import('@/pages/LiverPredict'));
const LungsPredictPage = lazy(() => import('@/pages/LungsPredict'));
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
                <Route path="/predict/diabetes" element={<DiabetesPredictPage />} />
                <Route path="/predict/heart" element={<HeartPredictPage />} />
                <Route path="/predict/kidney" element={<KidneyPredictPage />} />
                <Route path="/predict/liver" element={<LiverPredictPage />} />
                <Route path="/predict/lungs" element={<LungsPredictPage />} />
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
              </Route>

              {/* Fallback redirects to Dashboard */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </LanguageProvider>
    </ErrorBoundary>
  );
}
