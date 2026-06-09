# Contributing to EYTGaming

## Quick Start

See [DEVELOPER_QUICK_START.md](./DEVELOPER_QUICK_START.md) for local setup instructions.

## Branch Naming

- `feature/description` — New features
- `fix/description` — Bug fixes
- `chore/description` — Maintenance, tooling, CI
- `security/description` — Security patches
- `docs/description` — Documentation only

## Commit Messages

Follow the conventional commits format:

```
type(scope): description

Body (optional, explain the what and why)
```

Types: `feat`, `fix`, `security`, `refactor`, `test`, `docs`, `chore`, `style`, `perf`

Examples:
- `feat(tournaments): add Swiss system bracket generation`
- `fix(auth): prevent email enumeration on password reset`
- `security(2fa): enforce TOTP for admin accounts`

## Before Submitting a PR

1. **Run tests**: `pytest`
2. **Check lint**: `ruff check .`
3. **Check format**: `ruff format --check .`
4. **Run pre-commit**: `pre-commit run --all-files`
5. **Check security**: `pip-audit --requirement requirements.txt --strict`

## PR Process

1. Create a branch from `main`
2. Make your changes
3. Open a Pull Request against `main`
4. Ensure CI passes (lint, test, security scans)
5. Request a review
6. Merge after approval

## Code Standards

- Python 3.11+
- Django coding style (https://docs.djangoproject.com/en/5.2/internals/contributing/writing-code/coding-style/)
- Type hints required for all new code (`mypy --strict`)
- Maximum line length: 100 characters
- Quart-style imports (stdlib → Django → third-party → local)
- All views must have authentication/permission checks
- All user-supplied content must be sanitized (use `bleach` for HTML, `escape()` for strings)

## Security

- Never commit secrets, API keys, or passwords
- All state-changing endpoints require CSRF protection
- Rate limit all auth-related endpoints
- Sanitize all user input in views and model `clean()` methods
- Report security issues to security@eytgaming.com
