# Contributing to Steam Review Analyzer

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/steam-review-analyzer.git`
3. Create a virtual environment: `python3.12 -m venv .venv`
4. Activate it: `source .venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Create a feature branch: `git checkout -b feature/your-feature-name`

## Development Workflow

### Code Style

We follow PEP 8 with a few modifications:
- Max line length: 100 characters
- Use type hints for function arguments and return values
- Use descriptive variable names

### Testing

Before submitting a PR, ensure:
- All tests pass: `pytest src/tests/ -v`
- Code coverage is maintained: `pytest --cov=src/steam_review`
- No new linting errors: `ruff check src/`

### Commit Messages

Use clear, descriptive commit messages:
```
[TYPE] Brief description (50 chars max)

Detailed explanation if needed (wrap at 72 chars)

Related issues: #123
```

Types:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/updates
- `perf:` Performance improvements
- `chore:` Maintenance

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Fill out the PR template completely
5. Link related issues
6. Request review from maintainers

## Reporting Issues

When reporting bugs, include:
- Python version and OS
- How to reproduce the issue
- Expected vs actual behavior
- Any error messages/logs
- Screenshots if applicable

## Feature Requests

When requesting features, describe:
- The problem you're solving
- Your proposed solution
- Alternative approaches considered
- Why this feature is important

## Code Review Process

- Maintainers will review your PR within 7 days
- Address feedback promptly
- We may request changes before merging
- Once approved, your PR will be merged

## Recognition

Contributors will be:
- Added to CONTRIBUTORS.md
- Mentioned in release notes
- Credited in commit messages

## Questions?

- Open a discussion on GitHub
- Check existing issues and documentation
- Ask in commit messages or PR comments

## License

By contributing, you agree your code will be licensed under the MIT License.

Thank you for contributing!
