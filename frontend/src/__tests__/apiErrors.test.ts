import { ApiConnectionError, safeApiMessage } from '@/lib/apiErrors';

describe('API error helpers', () => {
  it('returns user-safe messages for known API errors', () => {
    expect(safeApiMessage(new ApiConnectionError('/profile'))).toBe(
      'Backend connection unavailable. Demo data may be incomplete.',
    );
    expect(safeApiMessage(new Error('Specific backend failure'))).toBe('Specific backend failure');
  });

  it('falls back for unknown or empty errors', () => {
    expect(safeApiMessage(new Error('   '))).toBe('Unable to load this clinical operations view.');
    expect(safeApiMessage(null)).toBe('Unable to load this clinical operations view.');
  });
});
