# Contributing to Delisushio

## Development Setup

### 1. Install pre-commit hooks (local validation)

Pre-commit hooks run automatically before each commit to catch issues early:

```bash
# Install pre-commit
poetry add --group dev pre-commit

# Install the git hooks
pre-commit install

# (Optional) Run all hooks on all files
pre-commit run --all-files
```

Once installed, the following checks will run on every commit:
- **Code formatting** (black, isort)
- **Linting** (flake8, pylint)
- **Code quality** (pyupgrade, trailing whitespace, etc.)

If a check fails, your commit is blocked. Fix the issues and try again.

### 2. Automated GitHub Actions (CI/CD)

When you push to `main` or `develop` (or open a pull request), GitHub automatically runs:
- ✅ Django system checks
- ✅ Full test suite (with PostgreSQL)
- ✅ Flake8 linting
- ✅ Pylint linting

**Check results:** Go to your repository → **Actions** tab to see workflow results.

### 3. GitHub branch protection rules (optional but recommended)

To require all checks pass before merging:

1. Go to **Settings** → **Branches**
2. Click **Add branch protection rule**
3. Branch name pattern: `main` (and/or `develop`)
4. Enable:
   - ✅ "Require a pull request before merging"
   - ✅ "Require status checks to pass before merging"
   - ✅ Select `test` workflow job
   - ✅ "Require branches to be up to date before merging"
5. **Save**

Now all checks must pass and PRs must be reviewed before merging.

## Skipping Checks (if needed)

### Skip pre-commit hooks
```bash
git commit --no-verify
```

### Skip GitHub Actions
Add `[skip ci]` to your commit message:
```bash
git commit -m "docs: update README [skip ci]"
```

## Testing Locally

Run tests before pushing:
```bash
# Full test suite
poetry run python manage.py test

# Specific test file
poetry run python manage.py test apps.orders.tests

# With verbose output
poetry run python manage.py test -v 2
```

## Code Quality

```bash
# Run all linting checks
pre-commit run --all-files

# Run specific checks
poetry run flake8 apps config --max-line-length=100
poetry run pylint apps --disable=missing-docstring,duplicate-code

# Format code (black + isort)
poetry run black apps config
poetry run isort apps config
```

## Troubleshooting

**Q: Pre-commit hooks won't install**
- Make sure `poetry install` was run first
- Run: `poetry run pre-commit install`

**Q: GitHub Actions failing with database errors**
- The workflow uses PostgreSQL in a service container
- Make sure your `manage.py test` works locally with PostgreSQL first

**Q: I see "file was modified by this hook" after committing**
- Black/isort modified your files. Review changes, stage them, and commit again.

