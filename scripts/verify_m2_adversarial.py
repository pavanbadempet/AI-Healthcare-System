#!/usr/bin/env python3
"""
Adversarial Verification & Stress Testing Suite for Milestone 2
Validates:
1. git fsck --full integrity across all 5 repositories
2. Release tags resolution, object types, and tagger attribution
3. 100% author/committer identity attribution across all branches & refs
4. Zero historical or unauthorized emails across commit headers, bodies, and refs
5. Historical timestamp ordering, date alignment (author vs committer), and tree validity
6. Parent DAG connectivity and root commit integrity
"""

import os
import re
import subprocess
import sys
from pathlib import Path

REPOS_DIR = Path(r"C:\Users\pavan\OneDrive\Documents\GitHub")
REPO_NAMES = [
    "sparklineage",
    "AI-Healthcare-System",
    "Movie-Recommendation-System",
    "omni-recommendation-companion",
    "pavanbadempet.github.io",
]

EXPECTED_NAME = "Pavan Badempet"
EXPECTED_EMAIL = "badempetp@gmail.com"

# Forbidden personal/legacy email patterns
FORBIDDEN_HISTORICAL_EMAILS = [
    "badempetpavan@gmail.com",
    "pavan9b@gmail.com",
    "pavanbadempet@gmail.com",
    "19wj1a0531@gniindia.org",
]

def run_git(cmd, repo_path):
    res = subprocess.run(
        ["git"] + cmd,
        cwd=repo_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    return res

def test_git_fsck(repo_path):
    res = run_git(["fsck", "--full"], repo_path)
    output = res.stdout + res.stderr
    errors = []
    dangling = 0
    for line in output.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue
        if line_clean.startswith("dangling "):
            dangling += 1
        elif "error:" in line_clean.lower() or "fatal:" in line_clean.lower() or "broken link" in line_clean.lower():
            errors.append(line_clean)
            
    passed = (len(errors) == 0 and res.returncode == 0)
    return passed, errors, dangling

def test_tags_and_taggers(repo_path):
    tags_res = run_git(["tag", "-l"], repo_path)
    tags = [t.strip() for t in tags_res.stdout.splitlines() if t.strip()]
    if not tags:
        return True, []
    
    tag_issues = []
    for tag in tags:
        commit_res = run_git(["rev-parse", "--verify", f"{tag}^{{commit}}"], repo_path)
        if commit_res.returncode != 0:
            tag_issues.append(f"Tag {tag} does NOT resolve to a commit")
            continue
            
        type_res = run_git(["cat-file", "-t", tag], repo_path)
        obj_type = type_res.stdout.strip()
        if obj_type == "tag":
            cat_res = run_git(["cat-file", "-p", tag], repo_path)
            tagger_line = ""
            for l in cat_res.stdout.splitlines():
                if l.startswith("tagger "):
                    tagger_line = l
                    break
            if EXPECTED_EMAIL not in tagger_line or EXPECTED_NAME not in tagger_line:
                tag_issues.append(f"Tag {tag} non-compliant tagger: {tagger_line}")
                
    passed = (len(tag_issues) == 0)
    return passed, tag_issues

def test_adversarial_attribution(repo_path):
    log_res = run_git(["log", "--all", "--format=%H|%an|%ae|%cn|%ce"], repo_path)
    lines = [l.strip() for l in log_res.stdout.splitlines() if l.strip()]
    
    non_compliant = []
    for line in lines:
        parts = line.split("|")
        if len(parts) != 5:
            continue
        h, an, ae, cn, ce = parts
        if an != EXPECTED_NAME or ae != EXPECTED_EMAIL or cn != EXPECTED_NAME or ce != EXPECTED_EMAIL:
            non_compliant.append((h, an, ae, cn, ce))
            
    return len(non_compliant) == 0, len(lines), non_compliant

def test_forbidden_emails_adversarial(repo_path):
    hdr_res = run_git(["log", "--all", "--format=%ae %ce"], repo_path)
    hdr_text = hdr_res.stdout
    body_res = run_git(["log", "--all", "--format=%s%n%b"], repo_path)
    body_text = body_res.stdout
    refs_res = run_git(["for-each-ref"], repo_path)
    refs_text = refs_res.stdout
    
    found_in_headers = [e for e in FORBIDDEN_HISTORICAL_EMAILS if e in hdr_text]
    found_in_bodies = [e for e in FORBIDDEN_HISTORICAL_EMAILS if e in body_text]
    found_in_refs = [e for e in FORBIDDEN_HISTORICAL_EMAILS if e in refs_text]
    
    passed = (len(found_in_headers) == 0 and len(found_in_bodies) == 0 and len(found_in_refs) == 0)
    return passed, found_in_headers, found_in_bodies, found_in_refs

def test_timestamps_and_trees(repo_path):
    log_res = run_git(["log", "--all", "--format=%H|%at|%ct|%T|%P"], repo_path)
    lines = [l.strip() for l in log_res.stdout.splitlines() if l.strip()]
    
    date_inversions = []
    empty_trees = []
    commit_set = set()
    parent_map = {}
    
    min_at = float("inf")
    max_at = float("-inf")
    
    for line in lines:
        parts = line.split("|")
        h = parts[0]
        at = int(parts[1])
        ct = int(parts[2])
        tree = parts[3]
        parents = parts[4].split() if len(parts) > 4 and parts[4] else []
        
        commit_set.add(h)
        parent_map[h] = parents
        
        min_at = min(min_at, at)
        max_at = max(max_at, at)
        
        if ct < at:
            date_inversions.append(h)
            
        if not tree or tree == "4b825dc642cb6eb9a060e54bf8d69288fbee4904":
            empty_trees.append(h)
            
    roots = [h for h, parents in parent_map.items() if not parents]
    missing_parents = [p for h, parents in parent_map.items() for p in parents if p not in commit_set]
    
    days_span = (max_at - min_at) / 86400.0 if lines else 0.0
    # Empty trees allowed only if < 5% of repository commits and matching authentic history
    trees_valid = (len(empty_trees) <= len(lines) * 0.05)
    passed = (len(date_inversions) == 0 and trees_valid and len(missing_parents) == 0 and len(roots) >= 1)
    
    return passed, len(date_inversions), len(empty_trees), len(roots), len(missing_parents), days_span

def main():
    print("=" * 80)
    print(" EMPIRICAL CHALLENGER VERIFICATION SUITE — MILESTONE 2")
    print(" Target Identity: Pavan Badempet <badempetp@gmail.com>")
    print("=" * 80)
    
    all_fsck_passed = True
    all_tags_passed = True
    all_attr_passed = True
    all_emails_passed = True
    all_dates_passed = True
    summary = {}
    
    for name in REPO_NAMES:
        repo_path = REPOS_DIR / name
        if not repo_path.exists():
            print(f"CRITICAL: Repository not found: {repo_path}")
            sys.exit(1)
            
        fsck_ok, fsck_errs, dangling = test_git_fsck(repo_path)
        tags_ok, tag_errs = test_tags_and_taggers(repo_path)
        attr_ok, commit_count, non_compliant = test_adversarial_attribution(repo_path)
        email_ok, found_hdrs, found_bodies, found_refs = test_forbidden_emails_adversarial(repo_path)
        dates_ok, inversions, empty_trees, roots, missing_p, span = test_timestamps_and_trees(repo_path)
        
        all_fsck_passed &= fsck_ok
        all_tags_passed &= tags_ok
        all_attr_passed &= attr_ok
        all_emails_passed &= email_ok
        all_dates_passed &= dates_ok
        
        summary[name] = {
            "commits": commit_count,
            "fsck": fsck_ok,
            "tags_ok": tags_ok,
            "attr_ok": attr_ok,
            "email_ok": email_ok,
            "dates_ok": dates_ok,
            "span_days": round(span, 1),
            "roots": roots,
            "missing_parents": missing_p
        }
        
    print("\n" + "=" * 80)
    print(" CHALLENGE VERIFICATION SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Repository':<32} | {'Commits':<7} | {'fsck':<5} | {'Tags':<5} | {'Attr':<5} | {'Emails':<6} | {'Dates':<5} | {'Roots':<5} | {'Span (d)':<8}")
    print("-" * 80)
    for name, s in summary.items():
        print(f"{name:<32} | {s['commits']:<7} | {'PASS' if s['fsck'] else 'FAIL':<5} | {'PASS' if s['tags_ok'] else 'FAIL':<5} | {'PASS' if s['attr_ok'] else 'FAIL':<5} | {'PASS' if s['email_ok'] else 'FAIL':<6} | {'PASS' if s['dates_ok'] else 'FAIL':<5} | {s['roots']:<5} | {s['span_days']:<8}")
    print("=" * 80)
    
    total_commits = sum(s["commits"] for s in summary.values())
    print(f"Total commits analyzed across 5 repositories: {total_commits}")
    
    overall_pass = all_fsck_passed and all_tags_passed and all_attr_passed and all_emails_passed and all_dates_passed
    verdict = "APPROVE" if overall_pass else "CHALLENGE_FAILED"
    print(f"\nFINAL VERDICT: {verdict}")
    
    if not overall_pass:
        sys.exit(1)

if __name__ == "__main__":
    main()
