"""
E2E Test Suite for Flagship Repositories Migration & Author History Rewriting.
Validates git attribution, historical timestamps, security sanitation, and remote synchronization.

Covers:
  - Tier 1: Feature Coverage (Attribution, Zero Legacy Emails, Target Repos, Branches/Tags)
  - Tier 2: Boundary & Corner Cases (Timestamps, Parent Lineage, Commit Consistency, Tree Integrity)
  - Tier 3: Cross-Feature & Security (Secret Scanner, .git/config Token Scrub, Remote URLs)
  - Tier 4: Real-World Scenarios (GitHub CLI Remote Sync, Tracking Branches, Tags, Offline Fallback)
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Generator, Tuple

import pytest

from scripts.run_migration_e2e import (
    EXPECTED_AUTHOR_EMAIL,
    EXPECTED_AUTHOR_NAME,
    EXPECTED_COMMITTER_EMAIL,
    EXPECTED_COMMITTER_NAME,
    FORBIDDEN_HISTORICAL_EMAILS,
    TARGET_GITHUB_NAMESPACE,
    TARGET_REPOSITORIES,
    CheckStatus,
    get_target_base_dir,
    run_live_audit,
    validate_tier1_attribution,
    validate_tier2_boundaries,
    validate_tier3_security,
    validate_tier4_realworld,
)

# Mark all tests in this file as e2e (registered in pytest.ini)
pytestmark = pytest.mark.e2e


@pytest.fixture
def compliant_git_repo() -> Generator[Path, None, None]:
    """Creates a temporary, fully compliant git repository mimicking post-migration state."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir)
        subprocess.run(["git", "init", "-b", "main"], cwd=str(repo_path), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", EXPECTED_AUTHOR_NAME], cwd=str(repo_path), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", EXPECTED_AUTHOR_EMAIL], cwd=str(repo_path), check=True, capture_output=True)

        env = os.environ.copy()
        # Commit 1: May 2023
        env["GIT_AUTHOR_DATE"] = "2023-05-10T10:00:00Z"
        env["GIT_COMMITTER_DATE"] = "2023-05-10T10:00:00Z"
        (repo_path / "README.md").write_text("# Healthcare System\nClinical AI Platform\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(repo_path), check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=str(repo_path), check=True, capture_output=True, env=env)

        # Commit 2: Feb 2024
        env["GIT_AUTHOR_DATE"] = "2024-02-15T14:00:00Z"
        env["GIT_COMMITTER_DATE"] = "2024-02-15T14:00:00Z"
        (repo_path / "main.py").write_text("print('FastAPI initialized')\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(repo_path), check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add API router"], cwd=str(repo_path), check=True, capture_output=True, env=env)

        # Release tag
        subprocess.run(["git", "tag", "-a", "v1.0.0", "-m", "Production release 1.0.0"], cwd=str(repo_path), check=True, capture_output=True, env=env)

        # Clean remote origin pointing to pavan-badempet
        remote_url = f"https://github.com/{TARGET_GITHUB_NAMESPACE}/compliant-sample.git"
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=str(repo_path), check=True, capture_output=True)

        yield repo_path


@pytest.fixture
def non_compliant_git_repo() -> Generator[Path, None, None]:
    """Creates a temporary non-compliant git repository containing legacy emails, leaked tokens, and bad origin."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir)
        subprocess.run(["git", "init", "-b", "main"], cwd=str(repo_path), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Legacy User"], cwd=str(repo_path), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "pavan9b@gmail.com"], cwd=str(repo_path), check=True, capture_output=True)

        env = os.environ.copy()
        # Commit with modern flattened timestamp (<10s spread)
        env["GIT_AUTHOR_DATE"] = "2026-10-16T12:00:00Z"
        env["GIT_COMMITTER_DATE"] = "2026-10-16T12:00:05Z"
        (repo_path / "README.md").write_text("# Legacy Project\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(repo_path), check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Legacy commit"], cwd=str(repo_path), check=True, capture_output=True, env=env)

        # Remote pointing to legacy un-migrated account
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/pavanbadempet/legacy.git"], cwd=str(repo_path), check=True, capture_output=True)

        # Leaked token in .git/config
        config_path = repo_path / ".git" / "config"
        content = config_path.read_text(encoding="utf-8")
        content += "\n[remote \"hf\"]\n\turl = https://user:hf_dummySecretTokenForTestScanners123456@huggingface.co/repo\n"
        config_path.write_text(content, encoding="utf-8")

        yield repo_path


# =====================================================================
# TIER 1: Feature Coverage Tests
# =====================================================================

def test_tier1_author_attribution_passes_when_all_commits_match(compliant_git_repo: Path) -> None:
    """Verifies that 100% commit author attribution passes when all commits match expected identity."""
    results = validate_tier1_attribution(compliant_git_repo, "test_repo")
    author_check = next(r for r in results if r.check_name == "author_attribution_100pct")
    assert author_check.status == CheckStatus.PASS
    assert "100% of commits" in author_check.message


def test_tier1_author_attribution_fails_when_legacy_author_present(non_compliant_git_repo: Path) -> None:
    """Verifies that author attribution fails if even a single commit has a non-matching author."""
    results = validate_tier1_attribution(non_compliant_git_repo, "test_repo")
    author_check = next(r for r in results if r.check_name == "author_attribution_100pct")
    assert author_check.status == CheckStatus.FAIL


def test_tier1_committer_attribution_passes_when_all_committers_match(compliant_git_repo: Path) -> None:
    """Verifies that 100% committer attribution passes when all committers match expected identity."""
    results = validate_tier1_attribution(compliant_git_repo, "test_repo")
    committer_check = next(r for r in results if r.check_name == "committer_attribution_100pct")
    assert committer_check.status == CheckStatus.PASS


def test_tier1_committer_attribution_fails_when_legacy_committer_present(non_compliant_git_repo: Path) -> None:
    """Verifies that committer attribution fails when historical or bot committer remains."""
    results = validate_tier1_attribution(non_compliant_git_repo, "test_repo")
    committer_check = next(r for r in results if r.check_name == "committer_attribution_100pct")
    assert committer_check.status == CheckStatus.FAIL


def test_tier1_zero_historical_emails_passes_when_clean(compliant_git_repo: Path) -> None:
    """Verifies zero presence of historical emails in a compliant repository."""
    results = validate_tier1_attribution(compliant_git_repo, "test_repo")
    email_check = next(r for r in results if r.check_name == "zero_historical_emails")
    assert email_check.status == CheckStatus.PASS


def test_tier1_zero_historical_emails_fails_when_forbidden_email_present(non_compliant_git_repo: Path) -> None:
    """Verifies that the presence of forbidden legacy emails triggers an explicit failure."""
    results = validate_tier1_attribution(non_compliant_git_repo, "test_repo")
    email_check = next(r for r in results if r.check_name == "zero_historical_emails")
    assert email_check.status == CheckStatus.FAIL
    assert "pavan9b@gmail.com" in str(email_check.details) or "legacy" in email_check.message.lower()


@pytest.mark.parametrize("target_repo_name", TARGET_REPOSITORIES)
def test_tier1_repository_presence_passes_for_all_five_targets(target_repo_name: str) -> None:
    """Verifies that all 5 required repositories exist on disk in the target directory."""
    base_dir = get_target_base_dir()
    repo_path = base_dir / target_repo_name
    assert repo_path.exists(), f"Target repository {target_repo_name} missing from {base_dir}"
    assert (repo_path / ".git").exists(), f"{target_repo_name} is not a valid git repository"


def test_tier1_repository_presence_fails_when_directory_missing() -> None:
    """Verifies that a non-existent repository path produces a FAIL CheckResult."""
    missing_path = Path("C:/invalid_nonexistent_repo_dir_12345")
    results = validate_tier1_attribution(missing_path, "missing_repo")
    assert any(r.status == CheckStatus.FAIL and r.check_name == "repo_dir_exists" for r in results)


def test_tier1_primary_branch_passes_when_main_or_master_active(compliant_git_repo: Path) -> None:
    """Verifies that primary branch check passes when active branch is main or master."""
    results = validate_tier1_attribution(compliant_git_repo, "test_repo")
    branch_check = next(r for r in results if r.check_name == "primary_branch_active")
    assert branch_check.status == CheckStatus.PASS
    assert "main" in branch_check.message


def test_tier1_release_tags_inventory_and_resolution(compliant_git_repo: Path) -> None:
    """Verifies that release tags are detected and logged in Tier 1 inventory."""
    results = validate_tier1_attribution(compliant_git_repo, "test_repo")
    tag_check = next(r for r in results if r.check_name == "tags_inventory")
    assert tag_check.status == CheckStatus.PASS
    assert "v1.0.0" in tag_check.message


# =====================================================================
# TIER 2: Boundary & Corner Cases Tests
# =====================================================================

def test_tier2_historical_timestamp_spread_passes_when_multi_year_history(compliant_git_repo: Path) -> None:
    """Verifies that historical dates spanning 2023 to 2024 pass date spread preservation."""
    results = validate_tier2_boundaries(compliant_git_repo, "test_repo")
    spread_check = next(r for r in results if r.check_name == "historical_date_spread")
    assert spread_check.status == CheckStatus.PASS
    assert "Historical timestamps span" in spread_check.message


def test_tier2_author_committer_date_alignment_passes_when_author_precedes_committer(compliant_git_repo: Path) -> None:
    """Verifies that author date <= committer date passes alignment check."""
    results = validate_tier2_boundaries(compliant_git_repo, "test_repo")
    order_check = next(r for r in results if r.check_name == "author_committer_alignment")
    assert order_check.status == CheckStatus.PASS


def test_tier2_commit_tree_integrity_passes_when_blobs_present(compliant_git_repo: Path) -> None:
    """Verifies that valid commit trees with file blobs pass tree integrity check."""
    results = validate_tier2_boundaries(compliant_git_repo, "test_repo")
    tree_check = next(r for r in results if r.check_name == "commit_tree_non_empty")
    assert tree_check.status == CheckStatus.PASS


def test_tier2_parent_graph_roots_passes_when_valid_lineage(compliant_git_repo: Path) -> None:
    """Verifies that commit parent graph has valid root commit pointers."""
    results = validate_tier2_boundaries(compliant_git_repo, "test_repo")
    graph_check = next(r for r in results if r.check_name == "parent_graph_roots")
    assert graph_check.status == CheckStatus.PASS
    assert "root commit" in graph_check.message


def test_tier2_tag_resolution_passes_when_annotated_and_lightweight_tags_valid(compliant_git_repo: Path) -> None:
    """Verifies that all tags resolve to valid commit objects in git history."""
    results = validate_tier2_boundaries(compliant_git_repo, "test_repo")
    tag_check = next(r for r in results if r.check_name == "tags_resolve_to_commits")
    assert tag_check.status == CheckStatus.PASS
    assert "All 1 tags resolve" in tag_check.message


# =====================================================================
# TIER 3: Cross-Feature Combinations & Security Tests
# =====================================================================

def test_tier3_git_config_token_free_passes_when_no_credentials(compliant_git_repo: Path) -> None:
    """Verifies that a clean .git/config passes token scrubbing validation."""
    results = validate_tier3_security(compliant_git_repo, "test_repo")
    config_check = next(r for r in results if r.check_name == "git_config_token_free")
    assert config_check.status == CheckStatus.PASS


def test_tier3_git_config_token_free_fails_when_hf_or_pat_token_present(non_compliant_git_repo: Path) -> None:
    """Verifies that leaked tokens in .git/config trigger immediate check failure."""
    results = validate_tier3_security(non_compliant_git_repo, "test_repo")
    config_check = next(r for r in results if r.check_name == "git_config_token_free")
    assert config_check.status == CheckStatus.FAIL
    assert "Leaked credentials in .git/config" in config_check.message


def test_tier3_origin_url_rebound_passes_when_matching_target_namespace(compliant_git_repo: Path) -> None:
    """Verifies that remote origin pointing to pavan-badempet passes rebinding check."""
    results = validate_tier3_security(compliant_git_repo, "test_repo")
    origin_check = next(r for r in results if r.check_name == "origin_url_rebound")
    assert origin_check.status == CheckStatus.PASS


def test_tier3_origin_url_rebound_fails_when_legacy_origin(non_compliant_git_repo: Path) -> None:
    """Verifies that remote origin pointing to legacy un-migrated account fails rebinding check."""
    results = validate_tier3_security(non_compliant_git_repo, "test_repo")
    origin_check = next(r for r in results if r.check_name == "origin_url_rebound")
    assert origin_check.status == CheckStatus.FAIL


def test_tier3_legacy_remotes_fails_when_unmigrated_remotes_exist(non_compliant_git_repo: Path) -> None:
    """Verifies that remotes referencing legacy username are caught and failed."""
    results = validate_tier3_security(non_compliant_git_repo, "test_repo")
    legacy_check = next(r for r in results if r.check_name == "no_legacy_remote_urls")
    assert legacy_check.status == CheckStatus.FAIL


def test_tier3_commit_messages_secret_free_passes_when_clean(compliant_git_repo: Path) -> None:
    """Verifies that clean commit messages pass pre-push secret scan."""
    results = validate_tier3_security(compliant_git_repo, "test_repo")
    msg_check = next(r for r in results if r.check_name == "commit_messages_secret_free")
    assert msg_check.status == CheckStatus.PASS


def test_tier3_lfs_config_clean_passes_when_clean(compliant_git_repo: Path) -> None:
    """Verifies that absent or clean .lfsconfig passes validation."""
    results = validate_tier3_security(compliant_git_repo, "test_repo")
    lfs_check = next(r for r in results if r.check_name == "lfs_config_clean")
    assert lfs_check.status == CheckStatus.PASS


# =====================================================================
# TIER 4: Real-World Scenarios Tests
# =====================================================================

def test_tier4_branch_sync_status_passes_when_clean(compliant_git_repo: Path) -> None:
    """Verifies that clean working tree and synced branch report PASS."""
    results = validate_tier4_realworld(compliant_git_repo, "test_repo", check_remote=False)
    sync_check = next(r for r in results if r.check_name == "branch_sync_status")
    assert sync_check.status == CheckStatus.PASS


def test_tier4_github_cli_auth_detects_login_state(compliant_git_repo: Path) -> None:
    """Verifies that GitHub CLI authentication status is probed cleanly."""
    results = validate_tier4_realworld(compliant_git_repo, "test_repo", check_remote=False)
    gh_check = next(r for r in results if r.check_name == "gh_cli_authenticated")
    assert gh_check.status in [CheckStatus.PASS, CheckStatus.WARN]


def test_tier4_remote_visibility_skipped_when_offline_or_local_only(compliant_git_repo: Path) -> None:
    """Verifies that remote API queries are skipped when check_remote is False."""
    results = validate_tier4_realworld(compliant_git_repo, "test_repo", check_remote=False)
    remote_check = next(r for r in results if r.check_name == "github_repo_exists")
    assert remote_check.status == CheckStatus.SKIP


def test_tier4_attribution_email_match_verifies_target_profile(compliant_git_repo: Path) -> None:
    """Verifies that attribution email matches the verified GitHub account email."""
    results = validate_tier4_realworld(compliant_git_repo, "test_repo", check_remote=False)
    profile_check = next(r for r in results if r.check_name == "attribution_email_match")
    assert profile_check.status == CheckStatus.PASS
    assert EXPECTED_AUTHOR_EMAIL in profile_check.message


# =====================================================================
# Live Audit Diagnostic Test
# =====================================================================

def test_live_migration_audit_report_generation() -> None:
    """Runs a full audit scan across all 5 live target repositories and verifies report structure."""
    live_report = run_live_audit(check_remote=False)
    # 5 repositories * ~21 checks each = 105 checks
    assert live_report.total_checks >= 100, f"Expected at least 100 checks across 5 repos, got {live_report.total_checks}"

    # Verify that all 5 target repositories are represented in the audit
    audited_repos = {r.repo for r in live_report.results}
    for target in TARGET_REPOSITORIES:
        assert target in audited_repos, f"Repository {target} was not audited in live report"

    # If MIGRATION_LIVE is set to 1, enforce strict 100% pass across all live repositories (Milestone 5)
    if os.getenv("MIGRATION_LIVE") == "1":
        assert live_report.is_successful(), f"Live migration has {live_report.failed} failures"
