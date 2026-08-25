/**
 * Edge Gateway Configuration Module
 * Reads and validates environment variables with safe production and local development defaults.
 */

export interface EdgeConfig {
  port: number;
  host: string;
  rustBackendUrl: string;
  rustWsUrl: string;
  jwtSecret: string;
  jwtAlgorithm: string;
  corsOrigins: string[];
  rateLimitPerMinute: number;
  rateLimitBurst: number;
  staticDir: string;
  enableStaticSpa: boolean;
  isTesting: boolean;
}

export function loadConfig(): EdgeConfig {
  const port = parseInt(process.env.PORT || '8000', 10);
  const host = process.env.HOST || '127.0.0.1';
  
  // Rust backend HTTP URL (default: http://127.0.0.1:8001)
  const rustBackendUrl = (
    process.env.RUST_BACKEND_URL || 
    process.env.BACKEND_URL || 
    'http://127.0.0.1:8001'
  ).replace(/\/+$/, '');

  // Rust backend WebSocket URL (default: ws://127.0.0.1:8001)
  const defaultWsUrl = rustBackendUrl
    .replace(/^http:\/\//, 'ws://')
    .replace(/^https:\/\//, 'wss://');
  const rustWsUrl = (process.env.RUST_WS_URL || defaultWsUrl).replace(/\/+$/, '');

  // JWT configuration
  const jwtSecret = process.env.SECRET_KEY || 'generate_a_secure_random_string_here';
  const jwtAlgorithm = process.env.ALGORITHM || 'HS256';

  // CORS allowed origins
  const corsRaw = process.env.CORS_ORIGINS || 'http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:8000';
  const corsOrigins = corsRaw.split(',').map(s => s.trim()).filter(Boolean);

  // Rate limiting settings
  const rateLimitPerMinute = parseInt(
    process.env.RATE_LIMIT_REQUESTS_PER_MINUTE || '100',
    10
  );
  const rateLimitBurst = parseInt(
    process.env.RATE_LIMIT_BURST || '20',
    10
  );

  // Static directory for Vite React SPA
  const staticDir = process.env.STATIC_DIR || '../frontend/dist';
  const enableStaticSpa = process.env.ENABLE_STATIC_SPA !== 'false';
  const isTesting = process.env.NODE_ENV === 'test' || process.env.TESTING === 'true';

  return {
    port,
    host,
    rustBackendUrl,
    rustWsUrl,
    jwtSecret,
    jwtAlgorithm,
    corsOrigins,
    rateLimitPerMinute,
    rateLimitBurst,
    staticDir,
    enableStaticSpa,
    isTesting,
  };
}

export const config = loadConfig();
