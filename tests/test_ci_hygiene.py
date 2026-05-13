from pathlib import Path


def test_ci_workflow_mirrors_uv_smoke_checks():
    workflow = Path(".github/workflows/ci.yml").read_text()

    assert "uv run --group dev pytest -q -p no:cacheprovider" in workflow
    assert "uv run python -m compileall -q podcast_auto_editor tests" in workflow
    assert "UV_CACHE_DIR: /tmp/uv-cache-podcast-auto-editor" in workflow
    assert "actions/upload-artifact" not in workflow
    assert ".omx" not in workflow


def test_release_hygiene_templates_exist_and_track_local_only_rules():
    changelog = Path("CHANGELOG.md").read_text()
    release_template = Path("docs/release-notes-template.md").read_text()
    pr_template = Path(".github/PULL_REQUEST_TEMPLATE.md").read_text()
    gitignore = Path(".gitignore").read_text()

    assert "## Unreleased" in changelog
    assert "Verification" in release_template
    assert "uv run --group dev pytest" in pr_template
    assert ".omx/" in gitignore
    assert ".omx" in pr_template


def test_readme_mentions_ci_and_release_hygiene():
    readme = Path("README.md").read_text()

    assert "GitHub Actions" in readme
    assert "CHANGELOG.md" in readme
    assert "docs/release-notes-template.md" in readme
