import { describe, expect, test, beforeAll, afterAll } from 'bun:test';
import { Database } from 'bun:sqlite';
import { existsSync, unlinkSync, rmdirSync, mkdirSync } from 'fs';
import { join } from 'path';
import {
  getDatabaseStatus,
  verifySchemaAndIntegrity,
  optimizeDatabase,
  vacuumDatabase,
  backupDatabase,
  restoreDatabase,
  runFullMaintenance,
  formatBytes,
} from './manage_db';

describe('manage_db.ts Unit Tests (Isolated Test Database)', () => {
  const TEST_DIR = join(import.meta.dir, '../temp_test_db_' + Date.now());
  const TEST_DB = join(TEST_DIR, 'test_healthcare.db');
  const TEST_BACKUPS = join(TEST_DIR, 'backups');
  const RESTORED_DB = join(TEST_DIR, 'test_restored.db');

  beforeAll(() => {
    mkdirSync(TEST_DIR, { recursive: true });
    mkdirSync(TEST_BACKUPS, { recursive: true });

    // Initialize isolated SQLite database
    const db = new Database(TEST_DB);
    db.run('PRAGMA journal_mode = WAL;');

    // Clinical tables matching schema
    db.run(`
      CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        role TEXT NOT NULL
      );
      CREATE TABLE departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
      );
      CREATE TABLE encounters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        encounter_type TEXT,
        status TEXT
      );
      CREATE TABLE vital_observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        heart_rate REAL,
        systolic_bp REAL,
        diastolic_bp REAL
      );
      CREATE TABLE prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER,
        status TEXT
      );
      CREATE TABLE beds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_id INTEGER NOT NULL,
        bed_number TEXT
      );
      CREATE TABLE audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_user_id INTEGER,
        admin_id INTEGER,
        action TEXT
      );
    `);

    // Insert sample records
    db.run("INSERT INTO users (username, role) VALUES ('dr_smith', 'doctor'), ('nurse_joy', 'nurse');");
    db.run("INSERT INTO departments (name) VALUES ('Cardiology'), ('Neurology');");
    for (let i = 1; i <= 20; i++) {
      db.run(`INSERT INTO vital_observations (patient_id, heart_rate, systolic_bp, diastolic_bp) VALUES (${1000 + i}, 72.0, 120.0, 80.0);`);
      db.run(`INSERT INTO encounters (patient_id, encounter_type, status) VALUES (${1000 + i}, 'AMB', 'finished');`);
      db.run(`INSERT INTO prescriptions (patient_id, status) VALUES (${1000 + i}, 'active');`);
    }

    db.close();
  });

  afterAll(() => {
    // Cleanup temporary files and directory
    try {
      if (existsSync(TEST_DB)) unlinkSync(TEST_DB);
      const wal = `${TEST_DB}-wal`;
      if (existsSync(wal)) unlinkSync(wal);
      const shm = `${TEST_DB}-shm`;
      if (existsSync(shm)) unlinkSync(shm);
      if (existsSync(RESTORED_DB)) unlinkSync(RESTORED_DB);
      const resWal = `${RESTORED_DB}-wal`;
      if (existsSync(resWal)) unlinkSync(resWal);
      const resShm = `${RESTORED_DB}-shm`;
      if (existsSync(resShm)) unlinkSync(resShm);

      if (existsSync(TEST_BACKUPS)) {
        const files = Bun.spawnSync(['pwsh', '-Command', `Remove-Item -Recurse -Force "${TEST_DIR}"`]);
      }
    } catch {
      // Ignore cleanup error
    }
  });

  test('formatBytes formats bytes into human-readable units', () => {
    expect(formatBytes(500)).toBe('500 B');
    expect(formatBytes(2048)).toBe('2.00 KB');
    expect(formatBytes(5 * 1024 * 1024)).toBe('5.00 MB');
  });

  test('getDatabaseStatus reports metadata, table row counts and integrity', () => {
    const status = getDatabaseStatus(TEST_DB);

    expect(status.exists).toBe(true);
    expect(status.integrity).toBe('ok');
    expect(status.foreignKeyOk).toBe(true);
    expect(status.tableCount).toBe(7);
    expect(status.tables['users']).toBe(2);
    expect(status.tables['vital_observations']).toBe(20);
    expect(status.tables['encounters']).toBe(20);
    expect(status.durationMs).toBeGreaterThanOrEqual(0);
  });

  test('getDatabaseStatus handles missing file gracefully', () => {
    const status = getDatabaseStatus('nonexistent_db_12345.db');
    expect(status.exists).toBe(false);
    expect(status.integrity).toBe('missing_file');
  });

  test('verifySchemaAndIntegrity confirms integrity and zero foreign key violations', () => {
    const check = verifySchemaAndIntegrity(TEST_DB);

    expect(check.ok).toBe(true);
    expect(check.integrity).toBe('ok');
    expect(check.foreignKeyOk).toBe(true);
    expect(check.foreignKeyViolations).toBe(0);
    expect(check.tables).toContain('vital_observations');
    expect(check.tables).toContain('prescriptions');
    expect(check.tables).toContain('beds');
    expect(check.durationMs).toBeLessThan(50);
  });

  test('optimizeDatabase creates clinical indices and tunes query planner', () => {
    const opt = optimizeDatabase(TEST_DB);

    expect(opt.success).toBe(true);
    expect(opt.createdIndices.length).toBeGreaterThan(0);
    expect(opt.durationMs).toBeLessThan(50);

    // Verify created indices exist in sqlite_master
    const db = new Database(TEST_DB, { readonly: true });
    const indices = db.query("SELECT name FROM sqlite_master WHERE type='index';").all() as { name: string }[];
    const indexNames = indices.map(i => i.name);
    db.close();

    expect(indexNames).toContain('idx_vital_observations_patient_id');
    expect(indexNames).toContain('idx_encounters_patient_id');
    expect(indexNames).toContain('idx_prescriptions_patient_id');
  });

  test('runFullMaintenance executes within <15ms requirement', () => {
    const maint = runFullMaintenance(TEST_DB);

    expect(maint.success).toBe(true);
    expect(maint.integrity).toBe('ok');
    expect(maint.foreignKeyOk).toBe(true);
    expect(maint.indicesChecked).toBeGreaterThan(0);
    expect(maint.durationMs).toBeLessThan(15); // Acceptance Criteria: <15ms
  });

  test('vacuumDatabase compacts pages and updates file metrics', () => {
    const vac = vacuumDatabase(TEST_DB);

    expect(vac.success).toBe(true);
    expect(vac.sizeAfter).toBeGreaterThan(0);
    expect(vac.durationMs).toBeGreaterThan(0);
  });

  test('backupDatabase and restoreDatabase perform atomic backup & validated restore', () => {
    const bkp = backupDatabase(TEST_DB, TEST_BACKUPS, 'test_backup.db');

    expect(bkp.success).toBe(true);
    expect(existsSync(bkp.destination)).toBe(true);
    expect(bkp.sizeBytes).toBeGreaterThan(0);

    // Restore backup to another database path
    const res = restoreDatabase(bkp.destination, RESTORED_DB);

    expect(res.success).toBe(true);
    expect(res.integrity).toBe('ok');
    expect(existsSync(RESTORED_DB)).toBe(true);

    // Verify restored database has identical tables and row counts
    const restoredStatus = getDatabaseStatus(RESTORED_DB);
    expect(restoredStatus.integrity).toBe('ok');
    expect(restoredStatus.tableCount).toBe(7);
    expect(restoredStatus.tables['vital_observations']).toBe(20);
    expect(restoredStatus.tables['users']).toBe(2);
  });
});
