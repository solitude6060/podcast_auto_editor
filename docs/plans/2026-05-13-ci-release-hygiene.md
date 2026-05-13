# CI and release hygiene increment

## Goal
Complete Phase A8 by adding repository-native CI/release hygiene that mirrors local uv verification and keeps OMX/local artifacts out of GitHub.

## Acceptance criteria
- GitHub Actions workflow runs uv-managed pytest and compileall on push/PR.
- Workflow does not upload artifacts from `.omx/` or require secrets/cloud credentials.
- Local smoke script remains the canonical command and is documented.
- Release notes template and changelog exist for future public releases.
- Tests assert the CI/release hygiene files preserve the expected commands and local-only exclusions.

## Files
- `.github/workflows/ci.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `CHANGELOG.md`
- `docs/release-notes-template.md`
- `tests/test_ci_hygiene.py`
- `README.md`
