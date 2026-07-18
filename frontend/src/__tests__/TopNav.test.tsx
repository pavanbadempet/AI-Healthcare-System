import {
  createElement as mockCreateElement,
  forwardRef as mockForwardRef,
  type ReactNode,
  type Ref,
} from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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

vi.mock('@/components/layout/CommandPalette', () => ({
  default: ({ open, onClose }: any) => open ? (
    <div>
      <input placeholder="Search patients, rooms, or tools..." />
      <button aria-label="Close search console" onClick={onClose}>Close search</button>
    </div>
  ) : null
}));

vi.mock('@/components/layout/MobileDrawer', () => ({
  default: () => <div>Mobile Drawer</div>
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

    // The title spans "AI Healthcare System" – multiple elements contain
    // this text (the h1 logo and the nav dropdown button), so use *AllBy*.
    const matches = screen.getAllByText(/AI Healthcare/i);
    expect(matches.length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/System/i).length).toBeGreaterThanOrEqual(1);
  });

  it('renders user information', () => {
    mockUseLocation.mockReturnValue({ pathname: '/' });

    render(<TopNav />);

    // Test Doctor should be rendered since we mocked the store
    expect(screen.getByText('Test Doctor')).toBeInTheDocument();
  });

  it('opens and closes the command menu when search button is clicked', async () => {
    mockUseLocation.mockReturnValue({ pathname: '/' });

    render(<TopNav />);

    // Command menu should not be visible initially
    expect(screen.queryByPlaceholderText(/Search patients, rooms, or tools/i)).not.toBeInTheDocument();

    // Find and click the search button
    const searchBtn = screen.getByRole('button', { name: /Open Command/i });
    fireEvent.click(searchBtn);

    // Command menu should now be visible
    const input = await screen.findByPlaceholderText(/Search patients, rooms, or tools/i);
    expect(input).toBeInTheDocument();

    // Click close button
    const closeBtn = screen.getByRole('button', { name: /Close search/i });
    fireEvent.click(closeBtn);

    // Command menu should be gone
    await waitFor(() => {
      expect(screen.queryByPlaceholderText(/Search patients, rooms, or tools/i)).not.toBeInTheDocument();
    });
  });
});
