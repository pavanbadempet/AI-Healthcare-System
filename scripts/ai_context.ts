/**
 * Session context snapshot for AI agents — Bun Native TypeScript Implementation.
 * 
 * Run at the start of any AI coding session to get a quick, ultra-fast overview
 * of the current project state in <50ms:
 * 
 *     bun scripts/ai_context.ts
 *     bun scripts/ai_context.ts --json
 */

import { existsSync, statSync, readdirSync } from 'node:fs';
import { resolve, join, basename, relative } from 'node:path';
import { homedir } from 'node:os';
import * as net from 'node:net';

const ROOT = resolve(import.meta.dir, '..');

const SERVICE_PORTS: [string, number][] = [
  ['Bun Edge Gateway', 8000],
  ['Rust Systems Core', 8001],
  ['Python Brain', 8002],
  ['Frontend (React 19)', 3000],
];

const CONTEXT_FILES = [
  'AGENTS.md',
  'backend/AGENTS.md',
  'frontend/AGENTS.md',
  'tests/AGENTS.md',
  'backend/CONTEXT.md',
  'CLAUDE.md',
  'GEMINI.md',
  '.github/copilot-instructions.md',
  '.cursor/rules/00-root.mdc',
  '.kiro/steering/structure.md',
  'docs/AI_AGENT_ARCHITECTURE.md',
  'scripts/agent_adapter_manifest.json',
  'scripts/sync_agent_adapters.py',
];

const ML_MODEL_FILES = [
  'backend/diabetes_model.pkl',
  'backend/heart_disease_model.pkl',
  'backend/liver_disease_model.pkl',
  'backend/liver_scaler.pkl',
  'backend/kidney_model.pkl',
  'backend/kidney_scaler.pkl',
  'backend/lungs_model.pkl',
  'backend/lungs_scaler.pkl',
];

function runCmd(cmd: string[]): string {
  try {
    const res = Bun.spawnSync(cmd, { cwd: ROOT });
    return res.stdout ? res.stdout.toString().trim() : '';
  } catch {
    return '';
  }
}

async function checkPort(port: number, host = '127.0.0.1'): Promise<boolean> {
  return new Promise((res) => {
    const socket = new net.Socket();
    socket.setTimeout(300);
    socket.on('connect', () => {
      socket.destroy();
      res(true);
    });
    socket.on('timeout', () => {
      socket.destroy();
      res(false);
    });
    socket.on('error', () => {
      res(false);
    });
    socket.connect(port, host);
  });
}

function pluginInfo() {
  const pluginsDir = join(homedir(), '.gemini', 'config', 'plugins');
  if (!existsSync(pluginsDir)) {
    return { exists: false, plugins: [], heavy_enabled_warnings: [] };
  }

  const plugins: { name: string; enabled: boolean }[] = [];
  const heavyEnabled: string[] = [];

  try {
    const entries = readdirSync(pluginsDir, { withFileTypes: true });
    for (const item of entries) {
      if (item.isDirectory()) {
        const name = item.name;
        if (name.startsWith('_') && name.endsWith('_DISABLED')) {
          plugins.push({ name: name.slice(1, -9), enabled: false });
        } else {
          plugins.push({ name, enabled: true });
          if (['science', 'android-cli-plugin'].includes(name.toLowerCase())) {
            heavyEnabled.push(name);
          }
        }
      }
    }
  } catch {}

  return { exists: true, plugins, heavy_enabled_warnings: heavyEnabled };
}

function databaseInfo() {
  const dbUrl = process.env.DATABASE_URL || 'sqlite:///./healthcare.db';
  const isPostgres = dbUrl.includes('postgresql');
  const info: any = {
    url: dbUrl,
    type: isPostgres ? 'postgresql' : 'sqlite',
  };

  if (!isPostgres) {
    const cleanPath = dbUrl.replace(/^sqlite:\/\/\/?/, '');
    const dbPath = cleanPath.startsWith('./') ? resolve(ROOT, cleanPath.slice(2)) : resolve(cleanPath);
    info.path = dbPath;
    info.exists = existsSync(dbPath);
    if (info.exists) {
      try {
        const sz = statSync(dbPath).size;
        info.size_mb = Math.round((sz / (1024 * 1024)) * 10) / 10;
      } catch {}
    }
  }
  return info;
}

function gitInfo() {
  const branch = runCmd(['git', 'branch', '--show-current']) || '(detached)';
  const log = runCmd(['git', 'log', '--oneline', '-5', '--no-decorate']);
  const dirty = runCmd(['git', 'status', '--porcelain', '-s']);

  return {
    branch,
    dirty_count: dirty ? dirty.split('\n').filter(Boolean).length : 0,
    recent_commits: log ? log.split('\n').filter(Boolean).slice(0, 5) : [],
  };
}

async function serviceInfo() {
  const services = [];
  for (const [name, port] of SERVICE_PORTS) {
    const running = await checkPort(port);
    services.append ? services.push({ name, host: '127.0.0.1', port, running }) : services.push({ name, host: '127.0.0.1', port, running });
  }
  return services;
}

function mlModelInfo() {
  const models = [];
  for (const rel of ML_MODEL_FILES) {
    const full = resolve(ROOT, rel);
    const exists = existsSync(full);
    if (exists) {
      const sz = statSync(full).size;
      models.push({
        name: basename(full),
        path: rel,
        exists: true,
        usable: sz > 0,
        size_mb: Math.round((sz / (1024 * 1024)) * 100) / 100,
      });
    } else {
      models.push({
        name: basename(rel),
        path: rel,
        exists: false,
        usable: false,
      });
    }
  }
  return models;
}

function contextFiles() {
  return CONTEXT_FILES.map((rel) => ({
    path: rel,
    exists: existsSync(resolve(ROOT, rel)),
  }));
}

async function buildSnapshot() {
  return {
    project: 'AI Healthcare System',
    database: databaseInfo(),
    git: gitInfo(),
    services: await serviceInfo(),
    ml_models: mlModelInfo(),
    context_files: contextFiles(),
    plugins: pluginInfo(),
    guidance_order: [
      'Read AGENTS.md first.',
      'Then read the nearest scoped AGENTS.md.',
      'Then read the matching CONTEXT.md only if you need deeper local detail.',
    ],
  };
}

async function main() {
  const args = process.argv.slice(2);
  const jsonOutput = args.includes('--json');

  const snapshot = await buildSnapshot();

  if (jsonOutput) {
    console.log(JSON.stringify(snapshot, null, 2));
    return;
  }

  console.log('='.repeat(70));
  console.log(`  AI HEALTHCARE SYSTEM — SESSION CONTEXT (BUN RUNTIME)`);
  console.log('='.repeat(70));

  console.log(`\n📌 Git: [${snapshot.git.branch}] ${snapshot.git.dirty_count} uncommitted changes`);
  for (const c of snapshot.git.recent_commits) {
    console.log(`   ${c}`);
  }

  console.log(`\n💾 Database: ${snapshot.database.type.toUpperCase()}`);
  if (snapshot.database.type === 'sqlite') {
    console.log(`   Path: ${snapshot.database.path} (${snapshot.database.exists ? `${snapshot.database.size_mb} MB` : 'NOT FOUND'})`);
  } else {
    console.log(`   URL: ${snapshot.database.url}`);
  }

  console.log(`\n🌐 Services:`);
  for (const s of snapshot.services) {
    const icon = s.running ? '🟢 RUNNING' : '⚪ STOPPED';
    console.log(`   ${icon.padEnd(12)} ${s.name.padEnd(25)} http://${s.host}:${s.port}`);
  }

  console.log(`\n🤖 ML Models:`);
  const present = snapshot.ml_models.filter((m: any) => m.exists);
  console.log(`   Found ${present.length}/${snapshot.ml_models.length} model artifacts.`);

  console.log(`\n📚 Guidance Surface:`);
  for (const g of snapshot.guidance_order) {
    console.log(`   → ${g}`);
  }
  console.log('='.repeat(70));
}

main().catch(console.error);
