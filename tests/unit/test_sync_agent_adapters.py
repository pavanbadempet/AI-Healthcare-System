import scripts.sync_agent_adapters as sync_agent_adapters


def test_build_generated_files_includes_scoped_wrappers():
    manifest = {
        "repo_name": "AI Healthcare System",
        "canonical_agents_file": "AGENTS.md",
        "wrapper_files": ["CLAUDE.md"],
        "scoped_wrapper_files": [
            {
                "path": "frontend/CLAUDE.md",
                "targets": ["../AGENTS.md", "./AGENTS.md"],
            }
        ],
        "cursor_legacy_shim_lines": [],
        "copilot_repo_lines": [],
        "cursor_root_rule": {
            "description": "Root rules",
            "lines": [],
            "refs": ["AGENTS.md"],
        },
        "scopes": [],
        "kiro": {"product": [], "tech": [], "structure": []},
    }

    files = sync_agent_adapters.build_generated_files(manifest)

    assert "frontend/CLAUDE.md" in files
    assert "@../AGENTS.md" in files["frontend/CLAUDE.md"]
    assert "@./AGENTS.md" in files["frontend/CLAUDE.md"]


def test_check_unmanaged_adapter_files_flags_unknown_tool_files(tmp_path, monkeypatch):
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
    monkeypatch.setattr(sync_agent_adapters, "ROOT", tmp_path)

    errors = sync_agent_adapters.check_unmanaged_adapter_files(
        generated_files={"CLAUDE.md": ""},
        manifest={"obsolete_files": []},
    )

    assert errors == ["unmanaged adapter file: frontend/CLAUDE.md"]


def test_check_generated_files_allows_missing_local_only_adapters(tmp_path, monkeypatch):
    monkeypatch.setattr(sync_agent_adapters, "ROOT", tmp_path)

    errors = sync_agent_adapters.check_generated_files(
        {
            "CLAUDE.md": "local only",
            ".cursor/rules/00-root.mdc": "local only",
            ".kiro/steering/tech.md": "local only",
            ".github/copilot-instructions.md": "tracked",
        }
    )

    assert errors == ["missing generated file: .github/copilot-instructions.md"]
