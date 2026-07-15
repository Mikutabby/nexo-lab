# Contributing to Nexo Ecosystem

Thanks for your interest in contributing! Here's how to get started.

## Quick Start

1. Fork the repository
2. Clone your fork
3. Create a feature branch: `git checkout -b my-feature`
4. Make your changes
5. Test your changes
6. Commit: `git commit -m "feat: add my feature"`
7. Push: `git push origin my-feature`
8. Open a Pull Request

## Development Setup

### Prerequisites
- Linux with bash and systemd
- ShellCheck (for linting)
- Python 3 (for some scripts)

### Local Testing
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/nexo-lab.git
cd nexo-lab

# Run ShellCheck on modified files
shellcheck -s bash install.sh

# Test the installer (dry run or in a VM)
./install.sh
```

## Code Style

### Shell Scripts
- Use `shellcheck` to validate your scripts
- Follow Google's Shell Style Guide
- Use meaningful variable names
- Add comments for complex logic
- Handle errors gracefully

### Python Scripts
- Follow PEP 8
- Use type hints where possible
- Add docstrings to functions

### Documentation
- Keep README.md in Spanish (primary language)
- Keep README.en.md in English (translations)
- Use clear, concise language
- Include examples when possible

## Commit Messages

Use conventional commits:
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `style:` — Code style changes (formatting, etc.)
- `refactor:` — Code refactoring
- `test:` — Adding tests
- `chore:` — Maintenance tasks

Examples:
```
feat: add new voice engine support
fix: resolve temperature monitor timeout
docs: update installation instructions
```

## Pull Request Guidelines

1. **One feature per PR** — Keep changes focused
2. **Test your changes** — Make sure they work
3. **Update documentation** — If adding features, update README
4. **Add yourself to contributors** — If this is your first contribution

## Reporting Issues

When reporting issues, please include:
- Distribution and version
- Steps to reproduce
- Expected behavior
- Actual behavior
- Relevant logs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Open an issue or reach out to [@Mikutabby](https://github.com/Mikutabby).
