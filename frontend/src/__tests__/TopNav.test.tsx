import {
  createElement as mockCreateElement,
  forwardRef as mockForwardRef,
  type ReactNode,
  type Ref,
} from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import TopNav from '@/components/layout/TopNav';
const mockUseLocation = vi.fn();
vi.mock('react-router-dom', () => ({
  Link: ({ children, to, ...props }: any) => <a href={to} {...props}>{children}</a>,
  useNavigate: () => vi.fn(),
  useLocation: () => mockUseLocation(),
}));

// Mock the Zustand store
vi.mock('@/lib/auth', () => ({
  useAuthStore: () => ({
    user: { username: 'testuser', role: 'doctor', full_name: 'Test Doctor' },
    logout: vi.fn(),
  }),
}));

// Mock framer-motion to disable async animations in tests
vi.mock('framer-motion', () => {
  const omittedMotionProps = new Set(['initial', 'animate', 'exit', 'transition', 'layoutId']);

  return {
    AnimatePresence: ({ children }: { children?: ReactNode }) => <>{children}</>,
    motion: new Proxy(
      {},
      {
        get: (_target, element) => {
          const tagName = String(element);
          const MotionComponent = mockForwardRef(
            ({ children, ...props }: { children?: ReactNode; [key: string]: unknown }, ref: Ref<HTMLElement>) => {
              const domProps = Object.fromEntries(
                Object.entries(props).filter(([key]) => !omittedMotionProps.has(key))
              );
              return mockCreateElement(tagName, { ...domProps, ref }, children);
            }
          );
          MotionComponent.displayName = `MockMotion.${tagName}`;
          return MotionComponent;
        },
      }
    ),
  };
});

describe('TopNav Component', () => {
  it('renders the TopNav logo and title', () => {
    mockUseLocation.mockReturnValue({ pathname: '/' });

    render(<TopNav />);

    // The title spans "AI Healthcare System"
    expect(screen.getByText(/AI Healthcare/i)).toBeInTheDocument();
    expect(screen.getByText(/System/i)).toBeInTheDocument();
  });

  it('renders user information', () => {
    mockUseLocation.mockReturnValue({ pathname: '/' });

    render(<TopNav />);

    // Test Doctor should be rendered since we mocked the store
    expect(screen.getByText('Test Doctor')).toBeInTheDocument();
  });

  it('opens and closes the command menu when search button is clicked', () => {
    mockUseLocation.mockReturnValue({ pathname: '/' });

    render(<TopNav />);

    // Command menu should not be visible initially
    expect(screen.queryByPlaceholderText(/Search modules, predictors/i)).not.toBeInTheDocument();

    // Find and click the search button
    const searchBtn = screen.getByRole('button', { name: /Open Command/i });
    fireEvent.click(searchBtn);

    // Command menu should now be visible
    const input = screen.getByPlaceholderText(/Search modules, predictors/i);
    expect(input).toBeInTheDocument();

    // Click close button
    const closeBtn = screen.getByRole('button', { name: /Close search/i });
    fireEvent.click(closeBtn);

    // Command menu should be gone
    expect(screen.queryByPlaceholderText(/Search modules, predictors/i)).not.toBeInTheDocument();
  });
});
