/**
 * CORS Middleware Configuration
 * Manages Cross-Origin Resource Sharing with strict origin verification and essential healthcare header forwarding.
 */

import { cors } from '@elysiajs/cors';
import { config } from '../config';

export function createCorsMiddleware() {
  return cors({
    origin: (request: Request): boolean => {
      const origin = request.headers.get('origin');
      if (!origin) return true; // Allow non-browser requests (cURL, mobile apps)
      
      // If wildcard or origins match
      if (config.corsOrigins.includes('*')) return true;
      if (config.corsOrigins.includes(origin)) return true;

      // Allow localhost / 127.0.0.1 origins in development
      if (
        origin.startsWith('http://localhost:') || 
        origin.startsWith('http://127.0.0.1:') ||
        origin.startsWith('https://localhost:') ||
        origin.startsWith('https://127.0.0.1:')
      ) {
        return true;
      }

      return false;
    },
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'],
    allowedHeaders: [
      'Content-Type',
      'Authorization',
      'Accept',
      'Origin',
      'X-Requested-With',
      'X-Request-ID',
      'X-Real-IP',
      'X-Forwarded-For',
      'X-AI-Provider',
      'X-AI-API-Key',
      'X-Facility-ID',
      'X-License-Key',
      'X-CSRF-Token',
      'Cache-Control',
      'Pragma',
    ],
    exposeHeaders: [
      'Content-Length',
      'Content-Type',
      'X-Request-ID',
      'X-Response-Time',
      'X-RateLimit-Limit',
      'X-RateLimit-Remaining',
      'X-RateLimit-Reset',
    ],
    credentials: true,
    maxAge: 86400,
  });
}
