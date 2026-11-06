# Project: Flagship Repositories Migration, Author History Rewriting & GitHub Synchronization

## Architecture

This project performs an automated, end-to-end migration, historical commit rewriting, security sanitization, and remote synchronization across 5 flagship repositories from legacy namespaces to LO's active GitHub account (`pavanbadempet`).

```
Target Repositories Directory: C:/Users/pavan/OneDrive/Documents/GitHub/
â”œâ”€â”€ sparklineage
â”œâ”€â”€ AI-Healthcare-System
â”œâ”€â”€ Movie-Recommendation-System
â”œâ”€â”€ omni-recommendation-companion
â””â”€â”€ pavanbadempet.github.io  (to remote: pavanbadempet/pavanbadempet.github.io)
```

Target Attribution Identity:
- **GitHub Username**: `pavanbadempet`
- **Author & Committer Name**: `Pavan Badempet`
- **Author & Committer Email**: `pavan9b@gmail.com`
- **Remote Origin Format**: `https://github.com/pavanbadempet/<repo>.git`

```
[ Local Repositories (5 targets) ]
               â”‚
               â–¼ Step 1: Health & Backup (M1)
[ Mirror Backups + Snapshot Commits of Dirty Trees ]
               â”‚
               â–¼ Step 2: Git Author Rewriting (M2)
[ python -m git_filter_repo --name-callback / --email-callback ]
  * Rewrites 100% commits to Pavan Badempet <pavan9b@gmail.com>
  * Preserves 100% original commit dates, author timestamps, commit trees
               â”‚
               â–¼ Step 3: Secret Sanitization (M3)
[ Pre-Push Secret Scanner & Token Scrub ]
  * Scrub leaked HF tokens from Movie-Recommendation-System .git/config
  * Verify 0 API keys, tokens, or private keys across all repos
               â”‚
               â–¼ Step 4: Remote Rebinding & Push (M4)
[ gh repo create + git remote set-url + git push --all / --tags ]
               â”‚
               â–¼ Step 5: Dual-Track E2E Test Suite & Audit (M5)
[ 100% Verified Attribution, Remote Sync, & Audit Clean ]
```

## Feature Inventory

Every feature from user requirements and survey handoffs:

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Working Tree Snapshot & Mirror Backup | Audit uncommitted files across all 5 repos, snapshot commit or stash cleanly, create mirror backups | M1 | Survey R1 |
| 2 | Sparklineage Rust Target Purge | Purge committed Rust target binary artifacts (`crates/sparklineage_core/target/`) and add to `.gitignore` | M1 | Survey R1 |
| 3 | Git History Author & Committer Rewrite | Execute `git-filter-repo` rewriting 100% author/committer emails to `pavan9b@gmail.com` and names to `Pavan Badempet` | M2 | Survey R2 |
| 4 | Timestamp & Tree Preservation | Preserve 100% original author dates, committer dates, and commit tree hashes across all branches & tags | M2 | Survey R2 |
| 5 | Token Scrub in .git/config | Remove plaintext Hugging Face token (`hf_tDkhAX...`) from `Movie-Recommendation-System/.git/config` remotes and LFS | M3 | Survey R3 |
| 6 | Automated Pre-Push Secret Scan | Execute multi-pattern secret scanner across all 5 codebases and commit logs (0 secrets tolerance) | M3 | Survey R3 |
| 7 | Remote Creation (`gh repo create`) | Create public remote repositories under `pavanbadempet` namespace via authenticated GitHub CLI | M4 | Survey R4 |
| 8 | Remote Rebinding & Synchronized Push | Configure `origin` to `https://github.com/pavanbadempet/<repo>.git`, push all branches (`--all`) and tags (`--tags`) | M4 | Survey R4 |
| 9 | E2E Migration Verification Suite | Automated test harness validating 100% commit author attribution, timestamp integrity, clean remotes, and push state | E2E Track | Original Request |
| 10 | Forensic Integrity Audit | Independent verification that no commits are missed, timestamps are preserved, and no secrets exist | Final Audit | Orchestration |

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Suite & Infrastructure | Test harness and test scripts validating attribution, timestamps, remotes, and security | none | IN_PROGRESS |
| M1 | Working Tree Health & Snapshot Backups | Clean/commit uncommitted working trees across all 5 repos, purge rust target in sparklineage, create mirror backups | none | PLANNED |
| M2 | Git Author & Historical Rewriting | Execute `python -m git_filter_repo` across all 5 repos for `Pavan Badempet <pavan9b@gmail.com>`, preserving dates | M1 | PLANNED |
| M3 | Pre-Push Secret & Sanitization Scan | Scrub `.git/config` tokens in Movie-Recommendation-System, run automated secret scan across all repos | M2 | PLANNED |
| M4 | Remote Rebinding & Synchronized Push | Create remotes on GitHub via `gh repo create`, rebind `origin`, and push all branches/tags | M3 | PLANNED |
| M5 | Final E2E Verification & Forensic Audit | Run 100% E2E test suite, pass Reviewer, Challenger, and Forensic Auditor gates | E2E, M4 | PLANNED |

## Interface Contracts

### Repository Naming & Namespace Mapping
- `sparklineage` -> `https://github.com/pavanbadempet/sparklineage.git`
- `AI-Healthcare-System` -> `https://github.com/pavanbadempet/AI-Healthcare-System.git`
- `Movie-Recommendation-System` -> `https://github.com/pavanbadempet/Movie-Recommendation-System.git`
- `omni-recommendation-companion` -> `https://github.com/pavanbadempet/omni-recommendation-companion.git`
- `pavanbadempet.github.io` -> `https://github.com/pavanbadempet/pavanbadempet.github.io.git`

### Rewriting Specification
- Tool: `python -m git_filter_repo`
- Callbacks:
  `--name-callback "return b'Pavan Badempet'"`
  `--email-callback "return b'pavan9b@gmail.com'"`
- Arguments: `--force`
- Invariant: Committer date == original committer date; Author date == original author date.

## Code Layout
```
C:/Users/pavan/OneDrive/Documents/GitHub/
â”œâ”€â”€ sparklineage/
â”œâ”€â”€ AI-Healthcare-System/
â”œâ”€â”€ Movie-Recommendation-System/
â”œâ”€â”€ omni-recommendation-companion/
â”œâ”€â”€ pavanbadempet.github.io/
â””â”€â”€ .backups_migration/               # Mirror backups before rewrite
```

