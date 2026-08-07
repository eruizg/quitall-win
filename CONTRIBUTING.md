# Contributing to QuitAll-Win

Thanks for your interest in contributing! This document covers what you
need to know to submit a useful pull request.

## Code of conduct

Be respectful, technical, and concise. Critique code, not people.

## Reporting bugs

Open a GitHub issue with:

- Windows version (`winver`)
- Python version if running from source
- QuitAll-Win version
- Steps to reproduce
- What you expected
- What you got (logs, screenshots welcome)

## Submitting changes

1. Fork the repo and create a topic branch from `main`.
2. Run the app from source (`pip install -e .` then `python -m quitall_win`).
3. Make your changes. Keep PRs focused — one feature or fix per PR.
4. Ensure `python -c "import ast, pathlib; [ast.parse(p.read_text()) for p in pathlib.Path('quitall_win').rglob('*.py')]"` passes.
5. Update the README if user-facing behavior changes.
6. Submit the PR with a clear description of *what* and *why*.

## Developer Certificate of Origin (DCO)

By contributing, you certify that you wrote the code or have the right
to submit it under the project's license. We enforce this via a sign-off
line on each commit:

```
git commit -s -m "Your commit message"
```

This appends `Signed-off-by: Your Name <your.email@example.com>` to the
commit, which is your DCO acknowledgment. PRs without sign-offs will be
asked to amend.

## License of contributions

All contributions are licensed under the GPL-3.0-or-later license, the
same as the rest of the project. By submitting a PR you agree to this.

The original author retains copyright over their contributions and the
project as a whole. Contributors retain copyright over their own
contributions.

## Scope of v1

For now we are deliberately keeping the scope narrow: **auto-quit unused
apps after a configurable idle time**, plus the minimum UI to configure
it. PRs that expand scope (manual quit lists, popup UIs, additional
triggers) are welcome but should first be discussed in an issue so we
can align on whether they fit the v1 vision.

## Architecture overview

See the "Architecture" section of the README. The codebase is small
(~600 lines) and intentionally so. Two Qt timers drive everything; no
threads.

When in doubt, prefer fewer features over more.
