# Legacy TUI status

The Textual TUI is preserved as an optional legacy interface, but it is **not** part of the Flask web application's normal runtime or CI/CD path.

- Web runtime: `requirements.txt`
- Optional TUI dependencies: `requirements-tui.txt`
- TUI command: `exerx-eye tui`
- GitHub CI: Flask + pytest + Playwright only
- HQ voice demo: manual `HQ Piper Demo` workflow only
- Legacy PyPI auto-publish: disabled

The old PyPI workflow is retained only as `.github/workflows/legacy-pypi-publish.yml.disabled` for reference. GitHub Actions does not execute that file.
