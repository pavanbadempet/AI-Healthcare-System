import { describe, it, expect } from 'bun:test';
import { JwtService } from '../src/middleware/jwt';

describe('JWT Verification & Auth Service', () => {
  const secret = 'super-secret-healthcare-key-32-chars-long';
  const jwt = new JwtService(secret);

  it('signs and verifies a valid JWT payload', async () => {
    const payload = {
      sub: 'doctor_alice',
      user_id: 42,
      role: 'doctor',
      facility_id: 101,
    };

    const token = await jwt.sign(payload, 3600);
    expect(token).toBeTruthy();
    expect(token.split('.').length).toBe(3);

    const { valid, payload: verifiedPayload, error } = await jwt.verify(token);
    expect(valid).toBe(true);
    expect(error).toBeUndefined();
    expect(verifiedPayload?.sub).toBe('doctor_alice');
    expect(verifiedPayload?.user_id).toBe(42);
    expect(verifiedPayload?.role).toBe('doctor');
    expect(verifiedPayload?.facility_id).toBe(101);
  });

  it('rejects expired JWT tokens', async () => {
    const payload = { sub: 'expired_user' };
    // Token with -10 seconds expiration (already expired)
    const token = await jwt.sign(payload, -10);

    const { valid, payload: verifiedPayload, error } = await jwt.verify(token);
    expect(valid).toBe(false);
    expect(error).toBe('Token expired');
    expect(verifiedPayload).toBeNull();
  });

  it('rejects tampered or forged tokens', async () => {
    const token = await jwt.sign({ sub: 'admin', role: 'admin' });
    const parts = token.split('.');
    
    // Tamper with payload (middle segment)
    const forgedPayload = btoa(JSON.stringify({ sub: 'hacker', role: 'superadmin' }));
    const tamperedToken = `${parts[0]}.${forgedPayload}.${parts[2]}`;

    const { valid, error } = await jwt.verify(tamperedToken);
    expect(valid).toBe(false);
    expect(error).toBeTruthy();
  });

  it('rejects tokens signed with a different secret', async () => {
    const foreignJwt = new JwtService('wrong-secret-key-different-signature');
    const token = await foreignJwt.sign({ sub: 'intruder' });

    const { valid } = await jwt.verify(token);
    expect(valid).toBe(false);
  });

  it('extracts tokens from Authorization headers and URL query', () => {
    const headers = new Headers({
      'Authorization': 'Bearer my-sample-jwt-token',
    });
    const extractedHeader = jwt.extractToken(headers);
    expect(extractedHeader).toBe('my-sample-jwt-token');

    const query = new URLSearchParams('token=query-token-abc');
    const extractedQuery = jwt.extractToken(new Headers(), query);
    expect(extractedQuery).toBe('query-token-abc');
  });
});
