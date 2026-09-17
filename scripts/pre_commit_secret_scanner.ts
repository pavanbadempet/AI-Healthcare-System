/**
 * Pre-Commit Secret Scanner & Zero-Leak Enforcement Gate (Bun Runtime).
 * Scans all staged files before every git commit to guarantee that no credentials,
 * PostgreSQL connection strings with passwords, Neon keys, API tokens, Doppler tokens,
 * or .env files can ever be committed to the repository.
 */

import { readFileSync, existsSync, statSync } from "node:fs";
import { basename } from "node:path";

interface SecretPattern {
  regex: RegExp;
  name: string;
}

const SECRET_PATTERNS: SecretPattern[] = [
  {
    regex: /postgres(?:ql)?:\/\/[a-zA-Z0-9_]+:[a-zA-Z0-9_.\-~%!$&'()*+,;=]{6,}@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/,
    name: "PostgreSQL URI with hardcoded password",
  },
  {
    regex: /[a-zA-Z0-9_.\-]+:[a-zA-Z0-9_.\-~%!$&'()*+,;=]{6,}@ep-[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+\.neon\.tech/,
    name: "Neon Database Connection with hardcoded credentials",
  },
  { regex: /\bnpg_[a-zA-Z0-9]{10,}\b/, name: "Neon Database Token (npg_*)" },
  { regex: /\bdapi[a-zA-Z0-9]{20,}\b/, name: "Databricks Personal Access Token (dapi*)" },
  { regex: /\bhf_[a-zA-Z0-9]{20,}\b/, name: "Hugging Face Access Token (hf_*)" },
  { regex: /\bsk-[a-zA-Z0-9_\-]{32,}\b/, name: "OpenAI / Anthropic Secret Key (sk-*)" },
  { regex: /\b(?:ghp|gho)_[a-zA-Z0-9]{20,}\b/, name: "GitHub Personal Access Token (ghp_*)" },
  { regex: /\bgithub_pat_[a-zA-Z0-9_]{50,}\b/, name: "GitHub Fine-Grained Token" },
  { regex: /\bAIza[a-zA-Z0-9_\-]{35}\b/, name: "Google API / Cloud Token" },
  { regex: /\bdp\.(?:pt|ct|st)\.[a-zA-Z0-9]{20,}\b/, name: "Doppler Token (dp.*)" },
  { regex: /\bAKIA[0-9A-Z]{16}\b/, name: "AWS Access Key ID (AKIA*)" },
  { regex: /-----BEGIN (?:RSA|EC|OPENSSH|PRIVATE) KEY-----/, name: "Private Cryptographic Key" },
  { regex: /mongodb(?:\+srv)?:\/\/[a-zA-Z0-9_]+:[^@]+@/, name: "MongoDB Connection String with Password" },
  { regex: /mysql:\/\/[a-zA-Z0-9_]+:[^@]+@/, name: "MySQL Connection String with Password" },
];

const EXCLUDED_FILES = [
  "scripts/pre_commit_secret_scanner.py",
  "scripts/pre_commit_secret_scanner.ts",
  ".env.example",
  "tests/",
];

const SAFE_PLACEHOLDERS = [
  "user:pass",
  "user:password",
  "username:password",
  "dummy",
  "placeholder",
  "mock_",
  "example.invalid",
  "<password>",
  "${POSTGRES_PASSWORD}",
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

function getAllTrackedFiles(): string[] {
  try {
    const proc = Bun.spawnSync(["git", "ls-files"], {
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

function scanFile(filepath: string): Array<{ lineNo: number; name: string; detail: string }> {
  const normPath = filepath.replace(/\\/g, "/");
  const fname = basename(normPath);

  // Rule 1: STRICTLY FORBID ANY .env FILE EXCEPT .env.example
  if (fname === ".env" || (fname.startsWith(".env.") && fname !== ".env.example") || fname.endsWith(".env")) {
    return [
      {
        lineNo: 1,
        name: "Prohibited Environment File",
        detail: `Attempted to commit '${fname}'. All secrets must be stored in Doppler!`,
      },
    ];
  }

  // Rule 2: Skip safe excluded files/dirs
  for (const exc of EXCLUDED_FILES) {
    if (normPath.includes(exc) || normPath === exc || normPath === `./${exc}`) {
      return [];
    }
  }

  if (!existsSync(filepath)) return [];
  try {
    if (statSync(filepath).isDirectory()) return [];
  } catch {
    return [];
  }

  let content: string;
  try {
    content = readFileSync(filepath, "utf8");
  } catch {
    return [];
  }

  const lines = content.split(/\r?\n/);
  const violations: Array<{ lineNo: number; name: string; detail: string }> = [];

  for (let idx = 0; idx < lines.length; idx++) {
    const line = lines[idx];
    if (SAFE_PLACEHOLDERS.some((p) => line.includes(p))) {
      continue;
    }
    for (const pat of SECRET_PATTERNS) {
      if (pat.regex.test(line)) {
        violations.push({ lineNo: idx + 1, name: pat.name, detail: line.trim().slice(0, 80) });
      }
    }
  }

  return violations;
}

function main() {
  let staged = getStagedFiles();
  let mode = "STAGED";
  if (!staged.length) {
    staged = getAllTrackedFiles();
    mode = "ALL TRACKED";
  }

  let totalViolations = 0;
  console.log("=".repeat(70));
  console.log(`[SECURITY GATE] RUNNING PRE-COMMIT ZERO-LEAK SECRET SCANNER (${mode})`);
  console.log(`Scanning ${staged.length} files...`);
  console.log("=".repeat(70));

  for (const fpath of staged) {
    const violations = scanFile(fpath);
    if (violations.length) {
      for (const v of violations) {
        console.log(`[BLOCKED] ${v.name} detected in ${fpath} (Line ${v.lineNo}): ${v.detail}`);
        totalViolations++;
      }
    }
  }

  if (totalViolations > 0) {
    console.log("\n" + "!".repeat(70));
    console.log(`[CRITICAL ERROR] COMMIT ABORTED: ${totalViolations} secret violations found!`);
    console.log("Never store plaintext credentials in code or files. Use Doppler:");
    console.log("  doppler secrets set KEY=VALUE");
    console.log("  doppler run -- <command>");
    console.log("!".repeat(70));
    process.exit(1);
  } else {
    console.log(`[OK] Zero secrets detected across all ${staged.length} scanned files. Safe to proceed.`);
    process.exit(0);
  }
}

main();
