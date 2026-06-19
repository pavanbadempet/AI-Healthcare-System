/**
 * Utility to prefetch dynamic page chunks before navigation.
 * When a user hovers over a link, we fetch the module chunk in the background.
 * The browser will cache it, allowing React.lazy to mount the page instantly.
 */
export const prefetchRoute = (path: string) => {
  // Strip query parameters and trailing slashes for routing matching
  const cleanPath = path.split('?')[0].replace(/\/$/, '');

  switch (cleanPath) {
    case '/dashboard':
      import('@/pages/Dashboard').catch(() => {});
      break;
    case '/patients':
      import('@/pages/Patients').catch(() => {});
      break;
    case '/chat':
      import('@/pages/Chat').catch(() => {});
      break;
    case '/telemedicine':
      import('@/pages/Telemedicine').catch(() => {});
      break;
    case '/predict':
      import('@/pages/Predict').catch(() => {});
      break;
    case '/predict/diabetes':
      import('@/pages/DiabetesPredict').catch(() => {});
      break;
    case '/predict/heart':
      import('@/pages/HeartPredict').catch(() => {});
      break;
    case '/predict/kidney':
      import('@/pages/KidneyPredict').catch(() => {});
      break;
    case '/predict/liver':
      import('@/pages/LiverPredict').catch(() => {});
      break;
    case '/predict/lungs':
      import('@/pages/LungsPredict').catch(() => {});
      break;
    case '/infrastructure':
      import('@/pages/Infrastructure').catch(() => {});
      break;
    case '/capacity':
      import('@/pages/Capacity').catch(() => {});
      break;
    case '/admin':
      import('@/pages/Admin').catch(() => {});
      break;
    case '/profile':
      import('@/pages/Profile').catch(() => {});
      break;
    case '/pricing':
      import('@/pages/Pricing').catch(() => {});
      break;
    case '/about':
      import('@/pages/About').catch(() => {});
      break;
    default:
      // Check if it matches a patient detail path: /patients/:id
      if (cleanPath.startsWith('/patients/')) {
        import('@/pages/PatientDetail').catch(() => {});
      }
      break;
  }
};
