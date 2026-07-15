# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-14

### Added
- **README in English** (`README.en.md`) for international contributors
- **CONTRIBUTING.md** with guidelines for contributors
- **GitHub Actions CI** with ShellCheck validation and structure checks
- **Dry-run mode** (`-n`/`--dry-run`) for safe testing before destructive operations
- **Non-interactive mode** (`-y`/`--non-interactive`) for automated installations
- **Dry-run helper** (`system/nexo-dryrun.sh`) with logging and confirmation prompts

### Security
- **Removed all sensitive data** from public repositories (tokens, passphrases, verification protocols)
- **Sanitized knowledge graph** and memory backups
- **Added `.gitignore` protection** for sensitive files in nexo-backups
- **ShellCheck fixes** for critical warnings in install.sh

### Changed
- **Install script** now supports `--dry-run` and `--non-interactive` flags
- **Shell scripts** cleaned up with ShellCheck (SC2086, SC2221/SC2222 fixed)

### Fixed
- Duplicate pattern in install.sh case statement (`voz|voice|voz` → `voice|voz`)
- Variable quoting issues in install.sh

## [Unreleased]

### In Progress
- Migrar say.sh (TTS) a Python
- Migrar nexo-backup.sh/restore a Python
- Docker support
- Enhanced testing suite

## [1.2.0] - 2026-07-14

### Added
- **voice.py v1.0** — Complete STT rewrite in Python with:
  - Multiple recording methods (parec, rec, arecord)
  - Voice Activity Detection (webrtcvad)
  - Echo detection
  - Multi-language support
  - Auto clipboard copy
- **Voice wrapper** for backward compatibility
- **say.py v1.0** — Complete TTS rewrite in Python with:
  - Multiple engines: Piper (offline), gTTS (cloud), espeak-ng (fallback)
  - Text preprocessing (markdown, URLs, emojis)
  - Multi-language support (es/en)
  - Adjustable speed
  - RAM-based temp files for reduced disk wear

## [1.1.0] - 2026-07-14

### Added
- **nexo-secrets v3.0** — Complete rewrite in Python with:
  - Better error handling
  - Structured logging
  - Export/import functionality
  - Automatic backups before import
  - Commands: get, set, check, delete, list, status, export, import
- **Wrapper script** for backward compatibility
