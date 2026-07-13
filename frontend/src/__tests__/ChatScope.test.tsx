import {
  createElement as mockCreateElement,
  forwardRef as mockForwardRef,
  type ReactNode,
  type Ref,
} from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import ChatCopilotPage from '@/pages/Chat';

const mockStreamChat = vi.fn();
let mockAuthUser = { username: 'patient_user', full_name: 'Patient User', role: 'patient' };

vi.mock('framer-motion', () => {
  const omittedMotionProps = new Set(['initial', 'animate', 'exit', 'transition']);

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

vi.mock('@/lib/auth', () => ({
  useAuthStore: () => ({
    user: mockAuthUser,
  }),
}));

vi.mock('react-markdown', () => ({
  __esModule: true,
  default: ({ children }: { children?: ReactNode }) => <>{children}</>,
}));

vi.mock('remark-gfm', () => ({
  __esModule: true,
  default: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  getChatHistory: vi.fn(() => Promise.resolve([])),
  clearChatHistory: vi.fn(() => Promise.resolve()),
  getChatSuggestions: vi.fn(() => Promise.resolve({ suggestions: [] })),
  streamChat: (...args: unknown[]) => mockStreamChat(...args),
}));

beforeEach(() => {
  window.HTMLElement.prototype.scrollIntoView = vi.fn();
  mockStreamChat.mockReset();
  mockStreamChat.mockImplementation((_message, _history, _onChunk, onDone) => {
    onDone();
    return vi.fn();
  });
  for (const key in mockAuthUser) delete (mockAuthUser as any)[key];
    Object.assign(mockAuthUser, { username: 'patient_user', full_name: 'Patient User', role: 'patient' });
});

async function renderChatPage() {
  const result = render(<ChatCopilotPage />);
  await act(async () => {
    await Promise.resolve();
  });
  return result;
}

function openSettings() {
  fireEvent.click(screen.getByRole('button', { name: /open settings panel/i }));
}

function sendMessage(message: string) {
  fireEvent.change(screen.getByLabelText(/type a message to the ai copilot/i), {
    target: { value: message },
  });
  fireEvent.click(screen.getByRole('button', { name: /send message/i }));
}

describe('chat RAG scope controls', () => {
  it('does not render unverified operational or compliance claims', async () => {
    const { container } = await renderChatPage();

    openSettings();
    const visibleText = container.textContent ?? '';
    const unverifiedClaims = [
      /FHIR data streams/i,
      /LATENCY:\s*34ms/i,
      /PHI PROTECTED/i,
      /NO DATA LOGGED EXTERNALLY/i,
      /GPT-4-Turbo-Med/i,
      /Online \(768d\)/i,
      /Vector DB:\s*Connected/i,
      /strictly sandboxed/i,
      /ensure evidence-based responses/i,
    ];

    for (const claim of unverifiedClaims) {
      expect(visibleText).not.toMatch(claim);
    }
  });

  it('keeps patient users on patient-scoped RAG', async () => {
    await renderChatPage();

    openSettings();
    expect(screen.queryByRole('radio', { name: /global db/i })).not.toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /active patient record/i })).toHaveAttribute('aria-checked', 'true');

    sendMessage('How are my diabetes records?');

    await waitFor(() => {
      expect(mockStreamChat).toHaveBeenCalled();
    });
    expect(mockStreamChat.mock.calls[0][5]).toBe('patient');
  });

  it('lets doctors opt into global RAG with the canonical scope value', async () => {
    for (const key in mockAuthUser) delete (mockAuthUser as any)[key];
    Object.assign(mockAuthUser, { username: 'doctor_user', full_name: 'Doctor User', role: 'doctor' });
    await renderChatPage();

    openSettings();
    const globalScope = screen.getByRole('radio', { name: /global db/i });
    fireEvent.click(globalScope);
    await waitFor(() => {
      expect(screen.getByRole('radio', { name: /global db/i })).toHaveAttribute('aria-checked', 'true');
    });
    sendMessage('Compare diabetes cases');

    await waitFor(() => {
      expect(mockStreamChat).toHaveBeenCalled();
    });
    expect(mockStreamChat.mock.calls[0][5]).toBe('global');
  });
});
