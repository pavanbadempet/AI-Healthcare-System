/**
 * Unified Healthcheck & Service Status Utility
 * Powered natively by Bun (bun:sqlite and native fetch) for sub-100ms execution.
 *
 * Usage:
 *   bun scripts/healthcheck.ts                # Human-readable service & DB status
 *   bun scripts/healthcheck.ts --json         # Machine-readable JSON output
 *   bun scripts/healthcheck.ts --db-only      # Check only SQLite database
 *   bun scripts/healthcheck.ts --services     # Check only HTTP services
 *   bun scripts/healthcheck.ts --timeout 200  # Per-probe timeout in ms
 */

import { Database } from 'bun:sqlite';
import { existsSync, statSync } from 'node:fs';
import { resolve } from 'node:path';

const ROOT = resolve(import.meta.dir, '..');

export interface ServiceTarget {
  name: string;
  url: string;
  critical: boolean;
}

export const DEFAULT_SERVICES: ServiceTarget[] = [
  { name: 'Bun Edge Gateway', url: 'http://127.0.0.1:8000/healthz/live', critical: false },
  { name: 'Rust Systems Core', url: 'http://127.0.0.1:8001/healthz', critical: false },
  { name: 'Python Brain', url: 'http://127.0.0.1:8002/healthz', critical: false },
  { name: 'Frontend (React 19)', url: 'http://127.0.0.1:3000', critical: false },
];

export interface ServiceProbeResult {
  name: string;
  url: string;
  status: 'UP' | 'DOWN' | 'DEGRADED';
  statusCode?: number;
  latencyMs: number;
  error?: string;
}

export interface DbHealthResult {
  path: string;
  type: 'sqlite' | 'postgresql';
  exists: boolean;
  sizeMb: number;
  integrity: 'OK' | 'CORRUPTED' | 'SKIPPED' | 'MISSING';
  journalMode?: string;
  tableCount: number;
  keyTablesFound: string[];
  latencyMs: number;
  error?: string;
}

export interface HealthcheckReport {
  timestamp: string;
  status: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY';
  executionTimeMs: number;
  database: DbHealthResult;
  services: ServiceProbeResult[];
}

export interface HealthcheckOptions {
  json?: boolean;
  dbOnly?: boolean;
  servicesOnly?: boolean;
  timeoutMs?: number;
  dbPath?: string;
  quiet?: boolean;
}

export function parseArgs(): HealthcheckOptions {
  const args = process.argv.slice(2);
  const options: HealthcheckOptions = {
    json: false,
    dbOnly: false,
    servicesOnly: false,
    timeoutMs: 250,
    quiet: false,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--json') {
      options.json = true;
    } else if (arg === '--db-only') {
      options.dbOnly = true;
    } else if (arg === '--services' || arg === '--services-only') {
      options.servicesOnly = true;
    } else if (arg === '--quiet' || arg === '-q') {
      options.quiet = true;
    } else if (arg === '--timeout' && i + 1 < args.length) {
      options.timeoutMs = parseInt(args[++i], 10) || 250;
    } else if (arg === '--db' && i + 1 < args.length) {
      options.dbPath = args[++i];
    } else if (arg === '--help' || arg === '-h') {
      console.log(`
AI Healthcare System — Unified Bun Healthcheck
Usage: bun scripts/healthcheck.ts [options]

Options:
  --json               Output machine-readable JSON status
  --db-only            Inspect only the SQLite database
  --services, --services-only Probe only the HTTP service endpoints
  --timeout <ms>       Per-service HTTP request timeout (default: 250 ms)
  --db <path>          Custom database path
  --quiet, -q          Suppress console output
  --help, -h           Show this help message
`);
      process.exit(0);
    }
  }

  return options;
}

export async function probeService(
  target: ServiceTarget,
  timeoutMs: number = 250
): Promise<ServiceProbeResult> {
  const startTime = performance.now();
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    const response = await fetch(target.url, {
      method: 'GET',
      signal: controller.signal,
      headers: { Accept: 'application/json, text/plain, */*' },
    });

    clearTimeout(timeoutId);
    const latencyMs = +(performance.now() - startTime).toFixed(2);

    if (response.ok) {
      return {
        name: target.name,
        url: target.url,
        status: 'UP',
        statusCode: response.status,
        latencyMs,
      };
    } else {
      return {
        name: target.name,
        url: target.url,
        status: 'DEGRADED',
        statusCode: response.status,
        latencyMs,
      };
    }
  } catch (err: any) {
    const latencyMs = +(performance.now() - startTime).toFixed(2);
    const isTimeout = err.name === 'AbortError' || err.message?.includes('aborted');
    return {
      name: target.name,
      url: target.url,
      status: 'DOWN',
      latencyMs,
      error: isTimeout ? `Timeout after ${timeoutMs}ms` : 'Connection refused / unreachable',
    };
  }
}

export function checkDatabase(customPath?: string): DbHealthResult {
  const startTime = performance.now();
  const dbUrl = process.env.DATABASE_URL || 'sqlite:///./healthcare.db';
  const isPostgres = dbUrl.startsWith('postgresql') || dbUrl.startsWith('postgres');

  let dbPath = customPath;
  if (!dbPath) {
    if (isPostgres) {
      const localFallback = resolve(ROOT, 'healthcare.db');
      if (existsSync(localFallback)) {
        dbPath = localFallback;
      } else {
        const latencyMs = +(performance.now() - startTime).toFixed(2);
        return {
          path: dbUrl.replace(/:[^:@]+@/, ':***@'),
          type: 'postgresql',
          exists: true,
          sizeMb: 0,
          integrity: 'SKIPPED',
          tableCount: 0,
          keyTablesFound: [],
          latencyMs,
        };
      }
    } else {
      const cleanPath = dbUrl.replace(/^sqlite:\/\/\/?/, '');
      dbPath = cleanPath.startsWith('./') ? resolve(ROOT, cleanPath.slice(2)) : resolve(cleanPath);
    }
  } else {
    dbPath = resolve(ROOT, dbPath);
  }

  if (!existsSync(dbPath)) {
    const latencyMs = +(performance.now() - startTime).toFixed(2);
    return {
      path: dbPath,
      type: 'sqlite',
      exists: false,
      sizeMb: 0,
      integrity: 'MISSING',
      tableCount: 0,
      keyTablesFound: [],
      latencyMs,
      error: 'Database file does not exist',
    };
  }

  try {
    const stat = statSync(dbPath);
    const sizeMb = +(stat.size / (1024 * 1024)).toFixed(2);

    const db = new Database(dbPath, { readonly: true });
    
    // Check integrity
    const integrityRow = db.query('PRAGMA quick_check;').get() as any;
    const quickCheck = Object.values(integrityRow || {})[0];
    const isOk = quickCheck === 'ok';

    // Check journal mode
    const journalRow = db.query('PRAGMA journal_mode;').get() as any;
    const journalMode = (Object.values(journalRow || {})[0] as string)?.toUpperCase();

    // Query tables
    const tableRows = db.query("SELECT name FROM sqlite_master WHERE type='table';").all() as { name: string }[];
    const allTables = new Set(tableRows.map((t) => t.name));

    const keyTables = ['hospital_facilities', 'departments', 'beds', 'users', 'prescriptions', 'vital_observations'];
    const keyTablesFound = keyTables.filter((kt) => allTables.has(kt));

    db.close();
    const latencyMs = +(performance.now() - startTime).toFixed(2);

    return {
      path: dbPath,
      type: 'sqlite',
      exists: true,
      sizeMb,
      integrity: isOk ? 'OK' : 'CORRUPTED',
      journalMode,
      tableCount: tableRows.length,
      keyTablesFound,
      latencyMs,
    };
  } catch (err: any) {
    const latencyMs = +(performance.now() - startTime).toFixed(2);
    return {
      path: dbPath,
      type: 'sqlite',
      exists: true,
      sizeMb: 0,
      integrity: 'CORRUPTED',
      tableCount: 0,
      keyTablesFound: [],
      latencyMs,
      error: err.message || 'SQLite access error',
    };
  }
}

export async function runHealthcheck(options: HealthcheckOptions = {}): Promise<HealthcheckReport> {
  const startTime = performance.now();
  const timeout = options.timeoutMs ?? 250;

  let dbResult: DbHealthResult;
  if (options.servicesOnly) {
    dbResult = {
      path: 'skipped',
      type: 'sqlite',
      exists: false,
      sizeMb: 0,
      integrity: 'SKIPPED',
      tableCount: 0,
      keyTablesFound: [],
      latencyMs: 0,
    };
  } else {
    dbResult = checkDatabase(options.dbPath);
  }

  let serviceResults: ServiceProbeResult[] = [];
  if (!options.dbOnly) {
    const probes = DEFAULT_SERVICES.map((srv) => probeService(srv, timeout));
    serviceResults = await Promise.all(probes);
  }

  const durationMs = +(performance.now() - startTime).toFixed(2);

  // Overall status evaluation
  const anyServiceUp = serviceResults.some((s) => s.status === 'UP');
  const allServicesUp = serviceResults.every((s) => s.status === 'UP');
  const dbHealthy = dbResult.integrity === 'OK' || dbResult.integrity === 'SKIPPED';

  let overallStatus: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY' = 'HEALTHY';
  if (!dbHealthy) {
    overallStatus = 'UNHEALTHY';
  } else if (!allServicesUp && anyServiceUp) {
    overallStatus = 'DEGRADED';
  } else if (!allServicesUp && serviceResults.length > 0) {
    overallStatus = 'DEGRADED'; // Local dev environment where backends are not running
  }

  return {
    timestamp: new Date().toISOString(),
    status: overallStatus,
    executionTimeMs: durationMs,
    database: dbResult,
    services: serviceResults,
  };
}

export function printReport(report: HealthcheckReport) {
  console.log('======================================================================');
  console.log('  AI HEALTHCARE SYSTEM — UNIFIED HEALTHCHECK (BUN)');
  console.log('======================================================================');
  console.log(`⏱️  Timestamp:       ${report.timestamp}`);
  console.log(`⚡ Execution Time:  ${report.executionTimeMs} ms`);
  console.log(`🛡️ Overall Status:  [${report.status}]`);
  console.log('----------------------------------------------------------------------');

  if (report.database.integrity !== 'SKIPPED') {
    console.log('📁 Database Health:');
    console.log(`   • Path:          ${report.database.path}`);
    console.log(`   • Type:          ${report.database.type.toUpperCase()}`);
    console.log(`   • Integrity:     [${report.database.integrity}]`);
    console.log(`   • Journal Mode:  ${report.database.journalMode || 'N/A'}`);
    console.log(`   • Table Count:   ${report.database.tableCount} tables`);
    console.log(`   • Size:          ${report.database.sizeMb} MB`);
    console.log(`   • Probe Latency: ${report.database.latencyMs} ms`);
    if (report.database.keyTablesFound.length > 0) {
      console.log(`   • Key Tables:    ${report.database.keyTablesFound.join(', ')}`);
    }
    console.log('----------------------------------------------------------------------');
  }

  if (report.services.length > 0) {
    console.log('🌐 Service Probes:');
    for (const srv of report.services) {
      const badge = srv.status === 'UP' ? '✅ [UP]' : srv.status === 'DEGRADED' ? '⚠️ [DEGRADED]' : '❌ [DOWN]';
      const detail = srv.statusCode ? `HTTP ${srv.statusCode}` : srv.error || 'N/A';
      console.log(`   • ${srv.name.padEnd(22)} : ${badge.padEnd(14)} (${detail}, ${srv.latencyMs} ms)`);
    }
    console.log('======================================================================');
  }
}

if (import.meta.main) {
  const options = parseArgs();
  runHealthcheck(options).then((report) => {
    if (options.json) {
      console.log(JSON.stringify(report, null, 2));
    } else if (!options.quiet) {
      printReport(report);
    }
  });
}
