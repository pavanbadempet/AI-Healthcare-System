/**
 * JWT Authentication & Verification Middleware
 * Fast native Web Crypto HS256 verification and guard for edge request validation.
 */

import { Elysia } from 'elysia';
import { config } from '../config';

export interface JwtPayload {
  sub?: string;
  user_id?: number | string;
  role?: string;
  facility_id?: string | number;
  exp?: number;
  iat?: number;
  [key: string]: any;
}

// Convert base64url to Uint8Array
function base64UrlToUint8Array(base64Url: string): Uint8Array {
  let base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  while (base64.length % 4 !== 0) {
    base64 += '=';
  }
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

// Convert Uint8Array to base64url
function uint8ArrayToBase64Url(bytes: Uint8Array): string {
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export class JwtService {
  private secret: string;
  private cryptoKey: CryptoKey | null = null;

  constructor(secret: string = config.jwtSecret) {
    this.secret = secret;
  }

  private async getKey(): Promise<CryptoKey> {
    if (!this.cryptoKey) {
      const encoder = new TextEncoder();
      const keyData = encoder.encode(this.secret);
      this.cryptoKey = await crypto.subtle.importKey(
        'raw',
        keyData,
        { name: 'HMAC', hash: 'SHA-256' },
        false,
        ['sign', 'verify']
      );
    }
    return this.cryptoKey;
  }

  public async sign(payload: JwtPayload, expiresInSeconds: number = 3600): Promise<string> {
    const key = await this.getKey();
    const now = Math.floor(Date.now() / 1000);
    const fullPayload: JwtPayload = {
      ...payload,
      iat: payload.iat || now,
      exp: payload.exp || now + expiresInSeconds,
    };

    const header = { alg: 'HS256', typ: 'JWT' };
    const encoder = new TextEncoder();

    const encodedHeader = uint8ArrayToBase64Url(encoder.encode(JSON.stringify(header)));
    const encodedPayload = uint8ArrayToBase64Url(encoder.encode(JSON.stringify(fullPayload)));
    const dataToSign = `${encodedHeader}.${encodedPayload}`;

    const signature = await crypto.subtle.sign(
      'HMAC',
      key,
      encoder.encode(dataToSign)
    );

    const encodedSignature = uint8ArrayToBase64Url(new Uint8Array(signature));
    return `${dataToSign}.${encodedSignature}`;
  }

  public async verify(token: string): Promise<{ valid: boolean; payload: JwtPayload | null; error?: string }> {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        return { valid: false, payload: null, error: 'Malformed token' };
      }

      const [headerB64, payloadB64, signatureB64] = parts;
      const key = await this.getKey();
      const encoder = new TextEncoder();

      const dataToVerify = `${headerB64}.${payloadB64}`;
      const signatureBytes = base64UrlToUint8Array(signatureB64);

      const isValid = await crypto.subtle.verify(
        'HMAC',
        key,
        signatureBytes,
        encoder.encode(dataToVerify)
      );

      if (!isValid) {
        return { valid: false, payload: null, error: 'Invalid signature' };
      }

      const payloadJson = new TextDecoder().decode(base64UrlToUint8Array(payloadB64));
      const payload: JwtPayload = JSON.parse(payloadJson);

      const now = Math.floor(Date.now() / 1000);
      if (payload.exp && payload.exp < now) {
        return { valid: false, payload: null, error: 'Token expired' };
      }

      return { valid: true, payload };
    } catch (e: any) {
      return { valid: false, payload: null, error: e.message || 'Token verification failed' };
    }
  }

  public extractToken(headers: Headers, urlQuery?: URLSearchParams): string | null {
    const authHeader = headers.get('authorization');
    if (authHeader && authHeader.startsWith('Bearer ')) {
      return authHeader.slice(7).trim();
    }
    if (urlQuery && urlQuery.has('token')) {
      return urlQuery.get('token');
    }
    return null;
  }
}

export const jwtService = new JwtService();

/**
 * Optional or transparent JWT verification middleware for edge routing
 */
export const jwtMiddleware = new Elysia({ name: 'middleware:jwt' })
  .derive({ as: 'global' }, async ({ request }) => {
    const url = new URL(request.url);
    const token = jwtService.extractToken(request.headers, url.searchParams);
    
    if (!token) {
      return { user: null, jwtToken: null };
    }

    const { valid, payload } = await jwtService.verify(token);
    if (valid && payload) {
      return { user: payload, jwtToken: token };
    }

    return { user: null, jwtToken: token };
  });
