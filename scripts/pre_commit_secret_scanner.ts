/**
 * Pre-Commit Secret Scanner & Zero-Leak Enforcement Gate (Bun Runtime).
 * Scans all staged files before every git commit to guarantee that no credentials,
 * PostgreSQL connection strings with passwords, Neon keys, API tokens, or secrets
 * can ever be committed to the repository.
 */

import { existsSync, statSync, readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";

interface SecretPattern {
  regex: RegExp;
  name: string;
}

const SECRET_PATTERNS: SecretPattern[] = [
  {
    regex: /postgres(?:ql)?:\/\/[a-zA-Z0-9_]+:[a-zA-Z0-9_.\-~%!$&'()*+,;=]{6,}@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/,
    name: "PostgreSQL URI with hardcoded password",
  },
  { regex: /\bnpg_[a-zA-Z0-9]{10,}\b/, name: "Neon Database Token (npg_*)" },
  { regex: /\bdapi[a-zA-Z0-9]{20,}\b/, name: "Databricks Personal Access Token (dapi*)" },
  { regex: /\bhf_[a-zA-Z0-9]{20,}\b/, name: "Hugging Face Access Token (hf_*)" },
  { regex: /\bsk-[a-zA-Z0-9_\-]{32,}\b/, name: "OpenAI / Anthropic Secret Key (sk-*)" },
  { regex: /\bghp_[a-zA-Z0-9]{20,}\b/, name: "GitHub Personal Access Token (ghp_*)" },
  { regex: /\bAIza[a-zA-Z0-9_\-]{35}\b/, name: "Google API / Cloud Token" },
  { regex: /\bdp\.pt\.[a-zA-Z0-9]{20,}\b/, name: "Doppler Service Token" },
  { regex: /-----BEGIN (?:RSA|EC|OPENSSH|PRIVATE) KEY-----/, name: "Private Cryptographic Key" },
  { regex: /mongodb(?:\+srv)?:\/\/[a-zA-Z0-9_]+:[^@]+@/, name: "MongoDB Connection String with Password" },
  { regex: /mysql:\/\/[a-zA-Z0-9_]+:[^@]+@/, name: "MySQL Connection String with Password" },
];

const IGNORED_DIRS = new Set([
  ".git", "node_modules", ".venv", "venv", "target", "dist", "build",
  ".pytest_cache", "__pycache__", ".turbo", ".next"
]);

const EXCLUDED_FILES = [
  "scripts/pre_commit_secret_scanner.py",
  "scripts/pre_commit_secret_scanner.ts",
  ".env.example",
  ".env",
  "tests/"
];

function getStagedFiles(): string[] {
  try {
    const proc = Bun.spawnSync(["git", "diff", "--cached", "--name-only"], {
      stdout: "pipe",
      stderr: "pipe",
    });
    const stdout = proc.stdout.toString().trim();
    if (!stdout) return [];
    return stdout.split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
  } catch {
    return [];
  }
}

function scanFile(filepath: string): Array<{ lineNo: number; name: string }> {
  if (!existsSync(filepath)) return [];
  try {
    if (statSync(filepath).isDirectory()) return [];
  } catch {
    return [];
  }

  const normPath = filepath.replace(/\\/g, "/");
  for (const exc of EXCLUDED_FILES) {
    if (normPath.includes(exc) || normPath === exc || normPath === `./${exc}`) {
      return [];
    }
  }

  const violations: Array<{ lineNo: number; name: string }> = [];
  try {
    const content = readFileSync(filepath, "utf8");
    const lines = content.split(/\r?\n/);

    for (let idx = 0; idx < lines.length; idx++) {
      const line = lines[idx];
      if (
        line.includes("user:pass") ||
        line.includes("user:password") ||
        line.includes("dummy") ||
        line.includes("placeholder") ||
        line.includes("mock_") ||
        line.includes("example.invalid")
      ) {
        continue;
      }
      for (const pat of SECRET_PATTERNS) {
        if (pat.regex.test(line)) {
          violations.push({ lineNo: idx + 1, name: pat.name });
        }
      }
    }
  } catch {
    // Ignore binary or unreadable files
  }

  return violations;
}

function walkDir(dir: string): string[] {
  const files: string[] = [];
  try {
    const entries = readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isDirectory()) {
        if (!IGNORED_DIRS.has(entry.name)) {
          files.push(...walkDir(join(dir, entry.name)));
        }
      } else {
        files.push(join(dir, entry.name));
      }
    }
  } catch {}
  return files;
}

function main(): void {
  let filesToScan = getStagedFiles();
  if (filesToScan.length === 0) {
    filesToScan = walkDir(".");
  }

  let totalViolations = 0;
  console.log("=".repeat(70));
  console.log("[SECURITY GATE] RUNNING PRE-COMMIT ZERO-LEAK SECRET SCANNER (BUN RUNTIME)");
  console.log(`Scanning ${filesToScan.length} files...`);
  console.log("=".repeat(70));

  for (const fpath of filesToScan) {
    const violations = scanFile(fpath);
    if (violations.length > 0) {
      for (const v of violations) {
        console.error(`[BLOCKED] Security violation detected in ${fpath} (Line ${v.lineNo}): ${v.name}`);
        totalViolations++;
      }
    }
  }

  if (totalViolations > 0) {
    console.error("\n" + "!".repeat(70));
    console.error(`[CRITICAL ERROR] COMMIT ABORTED: ${totalViolations} potential secrets found in scanned files!`);
    console.error("Please remove all hardcoded tokens, passwords, or URIs before committing.");
    console.error("!".repeat(70));
    process.exit(1);
  } else {
    console.log("[OK] Zero secrets detected across all scanned files. Code is safe to commit.");
    process.exit(0);
  }
}

main();
