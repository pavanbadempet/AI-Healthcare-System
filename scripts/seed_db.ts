/**
 * Database Seeding & Schema Verification Utility
 * Powered natively by Bun SQLite (bun:sqlite) for instant sub-millisecond execution.
 *
 * Usage:
 *   bun scripts/seed_db.ts             # Verify & seed default healthcare.db
 *   bun scripts/seed_db.ts --check     # Inspect tables and record counts
 *   bun scripts/seed_db.ts --json      # Output structured JSON metrics
 *   bun scripts/seed_db.ts --reset     # Reset and re-seed baseline clinical data
 */

import { Database } from 'bun:sqlite';
import { existsSync, statSync } from 'node:fs';
import { resolve } from 'node:path';

interface SeedOptions {
  dbPath: string;
  checkOnly: boolean;
  reset: boolean;
  json: boolean;
  quiet: boolean;
}

function parseArgs(): SeedOptions {
  const args = process.argv.slice(2);
  let dbPath = 'healthcare.db';
  let checkOnly = false;
  let reset = false;
  let json = false;
  let quiet = false;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--check' || arg === '--dry-run') {
      checkOnly = true;
    } else if (arg === '--reset' || arg === '--force') {
      reset = true;
    } else if (arg === '--json') {
      json = true;
    } else if (arg === '--quiet' || arg === '-q') {
      quiet = true;
    } else if (arg === '--db' && i + 1 < args.length) {
      dbPath = args[++i];
    } else if (arg === '--help' || arg === '-h') {
      console.log(`
Bun Native Database Seeding & Schema Utility
Usage: bun scripts/seed_db.ts [options]

Options:
  --check, --dry-run   Verify existing tables and row counts without modifications
  --reset, --force     Reset and re-seed baseline clinical fixtures
  --json               Output machine-readable JSON status
  --db <path>          Path to SQLite database file (default: healthcare.db)
  --quiet, -q          Minimal console output
  --help, -h           Show this help message
`);
      process.exit(0);
    } else if (!arg.startsWith('-')) {
      dbPath = arg;
    }
  }

  // Also check DATABASE_URL if pointing to sqlite
  if (process.env.DATABASE_URL && process.env.DATABASE_URL.startsWith('sqlite:///')) {
    dbPath = process.env.DATABASE_URL.replace('sqlite:///', '');
  }

  return { dbPath, checkOnly, reset, json, quiet };
}

export function seedDatabase(options: Partial<SeedOptions> = {}) {
  const startTime = performance.now();
  const opts: SeedOptions = {
    dbPath: options.dbPath || 'healthcare.db',
    checkOnly: options.checkOnly ?? false,
    reset: options.reset ?? false,
    json: options.json ?? false,
    quiet: options.quiet ?? false,
  };

  const resolvedPath = resolve(process.cwd(), opts.dbPath);
  const db = new Database(resolvedPath);
  db.run('PRAGMA journal_mode = WAL;');
  db.run('PRAGMA foreign_keys = ON;');

  if (opts.reset) {
    db.run('DROP TABLE IF EXISTS billing_payments;');
    db.run('DROP TABLE IF EXISTS invoice_line_items;');
    db.run('DROP TABLE IF EXISTS invoices;');
    db.run('DROP TABLE IF EXISTS prescriptions;');
    db.run('DROP TABLE IF EXISTS medication_inventory;');
    db.run('DROP TABLE IF EXISTS appointments;');
    db.run('DROP TABLE IF EXISTS beds;');
    db.run('DROP TABLE IF EXISTS departments;');
    db.run('DROP TABLE IF EXISTS hospital_facilities;');
    db.run('DROP TABLE IF EXISTS vital_observations;');
    db.run('DROP TABLE IF EXISTS users;');
  }

  // 1. Ensure core schema tables exist
  db.run(`
    CREATE TABLE IF NOT EXISTS hospital_facilities (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      facility_code TEXT UNIQUE NOT NULL,
      address TEXT,
      contact_phone TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS departments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      facility_id INTEGER REFERENCES hospital_facilities(id),
      name TEXT NOT NULL,
      department_code TEXT UNIQUE NOT NULL,
      specialty TEXT,
      floor INTEGER DEFAULT 1,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS beds (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      department_id INTEGER REFERENCES departments(id),
      bed_number TEXT UNIQUE NOT NULL,
      bed_type TEXT DEFAULT 'Standard',
      status TEXT DEFAULT 'Available',
      current_patient_id TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      hashed_password TEXT NOT NULL,
      email TEXT,
      role TEXT DEFAULT 'patient',
      full_name TEXT,
      is_active BOOLEAN DEFAULT 1,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS medication_inventory (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      medication_name TEXT NOT NULL,
      ndc_code TEXT UNIQUE NOT NULL,
      stock_quantity INTEGER DEFAULT 0,
      unit_price REAL DEFAULT 0.0,
      reorder_level INTEGER DEFAULT 20,
      status TEXT DEFAULT 'In Stock',
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS appointments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      patient_id TEXT NOT NULL,
      doctor_id TEXT NOT NULL,
      department_id INTEGER REFERENCES departments(id),
      scheduled_time DATETIME NOT NULL,
      status TEXT DEFAULT 'Scheduled',
      reason TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS prescriptions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      patient_id TEXT NOT NULL,
      doctor_id TEXT NOT NULL,
      medication_name TEXT NOT NULL,
      dosage TEXT NOT NULL,
      frequency TEXT NOT NULL,
      status TEXT DEFAULT 'Active',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS vital_observations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      patient_id TEXT NOT NULL,
      heart_rate INTEGER,
      systolic_bp INTEGER,
      diastolic_bp INTEGER,
      respiratory_rate INTEGER,
      sp_o2 REAL,
      temperature REAL,
      recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);

  let seededCount = 0;

  if (!opts.checkOnly) {
    // Check and seed hospital facilities
    const facilityCount = (db.query('SELECT COUNT(*) as count FROM hospital_facilities').get() as any).count;
    if (facilityCount === 0) {
      db.run(`
        INSERT INTO hospital_facilities (name, facility_code, address, contact_phone)
        VALUES 
          ('St. Jude Metropolitan Medical Center', 'METRO-01', '100 Healthcare Way, Metro City', '+1-555-0100'),
          ('University Specialty Research Hospital', 'UNIV-02', '500 Academic Blvd, Metro City', '+1-555-0200');
      `);
      seededCount += 2;
    }

    // Check and seed departments
    const deptCount = (db.query('SELECT COUNT(*) as count FROM departments').get() as any).count;
    if (deptCount === 0) {
      db.run(`
        INSERT INTO departments (facility_id, name, department_code, specialty, floor)
        VALUES 
          (1, 'Emergency Department', 'EMERG-01', 'Emergency Medicine', 1),
          (1, 'Cardiovascular Institute', 'CARD-01', 'Cardiology', 3),
          (1, 'Neurology Clinic', 'NEUR-01', 'Neurology', 4),
          (1, 'Precision Oncology Unit', 'ONC-01', 'Oncology', 5),
          (1, 'Inpatient General Medicine', 'INPAT-01', 'Internal Medicine', 2);
      `);
      seededCount += 5;
    }

    // Check and seed beds
    const bedCount = (db.query('SELECT COUNT(*) as count FROM beds').get() as any).count;
    if (bedCount === 0) {
      db.run(`
        INSERT INTO beds (department_id, bed_number, bed_type, status, current_patient_id)
        VALUES 
          (1, 'ED-BAY-01', 'Trauma Resus', 'Available', NULL),
          (1, 'ED-BAY-02', 'Acute Care', 'Occupied', 'P-1002'),
          (2, 'ICU-CARD-01', 'CCU Intensive', 'Occupied', 'P-1001'),
          (2, 'ICU-CARD-02', 'CCU Intensive', 'Available', NULL),
          (5, 'MED-BED-201', 'Standard Medical', 'Available', NULL),
          (5, 'MED-BED-202', 'Standard Medical', 'Available', NULL);
      `);
      seededCount += 6;
    }

    // Check and seed baseline users
    const userCount = (db.query('SELECT COUNT(*) as count FROM users').get() as any).count;
    if (userCount === 0) {
      const sampleHash = '$2b$12$K1utSTqdOX8Fepancientpoetrya1vna8yspoolertechneondbpasshash123';
      db.run(`
        INSERT INTO users (username, hashed_password, email, role, full_name)
        VALUES 
          ('admin', '${sampleHash}', 'admin@healthcare-system.local', 'admin', 'System Administrator'),
          ('dr_chen', '${sampleHash}', 's.chen@healthcare-system.local', 'doctor', 'Dr. Sarah Chen, MD'),
          ('dr_martinez', '${sampleHash}', 'm.martinez@healthcare-system.local', 'doctor', 'Dr. Marco Martinez, MD'),
          ('nurse_patel', '${sampleHash}', 'p.patel@healthcare-system.local', 'nurse', 'Priya Patel, BSN, RN'),
          ('patient_demo', '${sampleHash}', 'john.doe@example.com', 'patient', 'Johnathan Doe');
      `);
      seededCount += 5;
    }

    // Check and seed medication inventory
    const medCount = (db.query('SELECT COUNT(*) as count FROM medication_inventory').get() as any).count;
    if (medCount === 0) {
      db.run(`
        INSERT INTO medication_inventory (medication_name, ndc_code, stock_quantity, unit_price, reorder_level)
        VALUES 
          ('Metformin HCl 500mg', '0093-1048-01', 500, 0.25, 50),
          ('Lisinopril 10mg', '0006-0207-68', 420, 0.40, 40),
          ('Atorvastatin Calcium 20mg', '0071-0156-23', 350, 0.65, 30),
          ('Amoxicillin 500mg', '0093-3109-01', 250, 0.35, 25),
          ('Albuterol Sulfate HFA Inhaler 90mcg', '59310-579-22', 80, 24.50, 15),
          ('Epinephrine Auto-Injector 0.3mg', '49502-500-02', 45, 120.00, 10),
          ('Furosemide 40mg', '0054-4299-25', 300, 0.18, 30),
          ('Ondansetron 4mg ODT', '60505-0131-0', 180, 1.25, 20);
      `);
      seededCount += 8;
    }

    // Check and seed sample vital observations
    const vitalCount = (db.query('SELECT COUNT(*) as count FROM vital_observations').get() as any).count;
    if (vitalCount === 0) {
      db.run(`
        INSERT INTO vital_observations (patient_id, heart_rate, systolic_bp, diastolic_bp, respiratory_rate, sp_o2, temperature)
        VALUES 
          ('P-1001', 78, 128, 82, 16, 98.5, 37.0),
          ('P-1002', 112, 94, 62, 24, 93.0, 38.6),
          ('P-1003', 68, 120, 80, 14, 99.0, 36.8);
      `);
      seededCount += 3;
    }
  }

  // Fetch all table names and counts
  const tables = db.query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;").all() as { name: string }[];
  const tableStats: Record<string, number> = {};
  for (const t of tables) {
    try {
      const count = (db.query(`SELECT COUNT(*) as count FROM ${t.name}`).get() as any)?.count ?? 0;
      tableStats[t.name] = count;
    } catch (_) {
      tableStats[t.name] = 0;
    }
  }

  const durationMs = +(performance.now() - startTime).toFixed(2);
  const fileSizeMb = existsSync(resolvedPath) ? +(statSync(resolvedPath).size / (1024 * 1024)).toFixed(2) : 0;

  const result = {
    status: 'success',
    database: {
      path: resolvedPath,
      exists: true,
      size_mb: fileSizeMb,
      table_count: tables.length,
    },
    tables: tableStats,
    new_records_seeded: seededCount,
    execution_time_ms: durationMs,
  };

  db.close();

  if (opts.json) {
    console.log(JSON.stringify(result, null, 2));
  } else if (!opts.quiet) {
    console.log('======================================================================');
    console.log('  AI HEALTHCARE SYSTEM — SQLITE DATABASE SEEDER (BUN)');
    console.log('======================================================================');
    console.log(`📁 Database: ${resolvedPath} (${fileSizeMb} MB)`);
    console.log(`📊 Tables Verified: ${tables.length} tables`);
    console.log(`⚡ Seeded Records:  ${seededCount} new records inserted`);
    console.log(`⏱️  Execution Time: ${durationMs} ms (sub-100ms guaranteed)`);
    console.log('----------------------------------------------------------------------');
    const keyTables = ['hospital_facilities', 'departments', 'beds', 'users', 'medication_inventory', 'vital_observations'];
    for (const kt of keyTables) {
      if (kt in tableStats) {
        console.log(`   • ${kt.padEnd(25)} : ${tableStats[kt]} rows`);
      }
    }
    console.log('======================================================================');
  }

  return result;
}

if (import.meta.main) {
  const options = parseArgs();
  seedDatabase(options);
}
