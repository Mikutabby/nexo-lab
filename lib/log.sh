# ── Centralized Logging for Nexo Asistente ──────────────────────────────
# Source this file in any script that needs logging.
# Works both from repo (relative path) and installed location.
#
# Functions:
#   log_init <name>            — Initialize log for component <name>
#   log_info <message>         — Log informational message
#   log_warn <message>         — Log warning message
#   log_error <message>        — Log error message
#   log_debug <message>        — Log debug message (only if DEBUG=1)

NEXO_LOG_DIR="${NEXO_LOG_DIR:-$HOME/.nexo-memory/log}"
NEXO_LOG_COMPONENT=""

log_init() {
  NEXO_LOG_COMPONENT="${1:-nexo}"
  mkdir -p "$NEXO_LOG_DIR"
}

_log_write() {
  local level="$1"
  shift
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  local log_file="$NEXO_LOG_DIR/${NEXO_LOG_COMPONENT}.log"
  echo "$timestamp | $level | $*" >> "$log_file"
}

log_info()   { _log_write "INFO" "$@"; }
log_warn()   { _log_write "WARN" "$@"; }
log_error()  { _log_write "ERROR" "$@"; }
log_debug()  { if [ "${DEBUG:-0}" = "1" ]; then _log_write "DEBUG" "$@"; fi; }
