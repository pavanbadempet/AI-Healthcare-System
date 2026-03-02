import { render, screen } from '@testing-library/react';
import TopNav from '@/components/layout/TopNav';
import { usePathname } from 'next/navigation';

// Mock the Next.js router and hooks
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

// Mock the Zustand store
jest.mock('@/lib/auth', () => ({
  useAuthStore: () => ({
    user: { username: 'testuser', role: 'doctor', full_name: 'Test Doctor' },
    logout: jest.fn(),
  }),
}));

describe('TopNav Component', () => {
  it('renders the TopNav logo and title', () => {
    (usePathname as jest.Mock).mockReturnValue('/');
    
    render(<TopNav />);
    
    // The title spans "AI Healthcare System"
    expect(screen.getByText(/AI Healthcare/i)).toBeInTheDocument();
    expect(screen.getByText(/System/i)).toBeInTheDocument();
  });

  it('renders user information', () => {
    (usePathname as jest.Mock).mockReturnValue('/');
    
    render(<TopNav />);
    
    // Test Doctor should be rendered since we mocked the store
    expect(screen.getByText('Test Doctor')).toBeInTheDocument();
  });
});
