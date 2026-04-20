#!/bin/bash
# Scheduled Ralph - Usage-aware Claude Code loop
# Uses Claude Code OAuth API for accurate usage tracking
# Requires: jq, curl
#
# Usage: ./scheduled-ralph.sh [options] [max_iterations]
#
# Options:
#   --max-usage <percent>   Stop when block usage reaches this % (0 = no limit)
#   --wait-next-session     Wait for next 5-hour session before starting
#   --wait                  Wait for next block if usage is too high during run
#   --wait-threshold <pct>  Start waiting when usage exceeds this % (default: 90)
#   --check-interval <sec>  How often to check usage when waiting (default: 300)
#   --dry-run               Show what would happen without running
#   --quiet                 Suppress progress messages

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
MAX_ITERATIONS=10
MAX_USAGE_PERCENT=0
WAIT_NEXT_SESSION=false
WAIT_FOR_USAGE=false
WAIT_THRESHOLD=90
CHECK_INTERVAL=300
DRY_RUN=false
QUIET=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --max-usage)
      MAX_USAGE_PERCENT="$2"
      shift 2
      ;;
    --wait-next-session)
      WAIT_NEXT_SESSION=true
      shift
      ;;
    --wait)
      WAIT_FOR_USAGE=true
      shift
      ;;
    --wait-threshold)
      WAIT_THRESHOLD="$2"
      shift 2
      ;;
    --check-interval)
      CHECK_INTERVAL="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --quiet|-q)
      QUIET=true
      shift
      ;;
    --help|-h)
      echo "Scheduled Ralph - Usage-aware Claude Code loop"
      echo ""
      echo "Usage: $0 [options] [max_iterations]"
      echo ""
      echo "Options:"
      echo "  --max-usage <percent>     Stop when block usage reaches this % (0 = no limit)"
      echo "  --wait-next-session       Wait for next 5-hour session before starting"
      echo "  --wait                    Wait for next block if usage is too high during run"
      echo "  --wait-threshold <pct>    Start waiting when usage exceeds this % (default: 90)"
      echo "  --check-interval <sec>    How often to check usage when waiting (default: 300)"
      echo "  --dry-run                 Show what would happen without running"
      echo "  --quiet                   Suppress progress messages"
      echo ""
      echo "Examples:"
      echo "  $0 5                              # Run 5 iterations, no usage limits"
      echo "  $0 --max-usage 70 5               # Run 5 iterations, stop at 70% usage"
      echo "  $0 --wait-next-session 10         # Wait for next session, then run 10 iterations"
      echo "  $0 --max-usage 80 --wait 10       # Stop at 80%, wait if needed"
      exit 0
      ;;
    -*)
      echo "Unknown option: $1"
      exit 1
      ;;
    *)
      MAX_ITERATIONS="$1"
      shift
      ;;
  esac
done

log() {
  if [ "$QUIET" = false ]; then
    echo "$@"
  fi
}

log_status() {
  if [ "$QUIET" = false ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════════"
  fi
}

# Check required dependencies
check_dependencies() {
  if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not found. Install with: brew install jq"
    exit 1
  fi
  if ! command -v curl &> /dev/null; then
    echo "Error: curl is required but not found."
    exit 1
  fi
}

# Get OAuth token from macOS Keychain or Linux config
get_oauth_token() {
  local creds token

  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS: get from Keychain
    creds=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null)
    if [ -z "$creds" ]; then
      echo ""
      return
    fi
    token=$(echo "$creds" | jq -r '.claudeAiOauth.accessToken // empty' 2>/dev/null)
  else
    # Linux: try config file
    local config_file="$HOME/.config/claude-code/auth.json"
    if [ -f "$config_file" ]; then
      token=$(jq -r '.claudeAiOauth.accessToken // empty' "$config_file" 2>/dev/null)
    fi
  fi

  echo "$token"
}

# Fetch usage data from Claude Code OAuth API
fetch_usage_api() {
  local token="$1"
  if [ -z "$token" ]; then
    echo ""
    return
  fi

  curl -s -f "https://api.anthropic.com/api/oauth/usage" \
    -H "Authorization: Bearer $token" \
    -H "anthropic-beta: oauth-2025-04-20" \
    -H "User-Agent: scheduled-ralph/1.0" 2>/dev/null
}

# Cache for OAuth token (avoid repeated Keychain lookups)
CACHED_TOKEN=""

# Get usage data from OAuth API
get_usage_data() {
  # Get OAuth token (cache it)
  if [ -z "$CACHED_TOKEN" ]; then
    CACHED_TOKEN=$(get_oauth_token)
  fi

  if [ -n "$CACHED_TOKEN" ]; then
    fetch_usage_api "$CACHED_TOKEN"
  else
    echo ""
  fi
}

# Extract 5-hour usage percentage from API data
get_usage_percent() {
  local json="$1"

  if [ -z "$json" ]; then
    echo "-1"
    return
  fi

  local api_percent
  api_percent=$(echo "$json" | jq -r '.five_hour.utilization // empty' 2>/dev/null)

  if [ -n "$api_percent" ] && [ "$api_percent" != "null" ]; then
    printf "%.1f" "$api_percent"
    return
  fi

  echo "-1"
}

# Get 7-day usage percentage
get_weekly_percent() {
  local json="$1"

  if [ -z "$json" ]; then
    echo "-1"
    return
  fi

  local weekly_percent
  weekly_percent=$(echo "$json" | jq -r '.seven_day.utilization // empty' 2>/dev/null)

  if [ -n "$weekly_percent" ] && [ "$weekly_percent" != "null" ]; then
    printf "%.1f" "$weekly_percent"
    return
  fi

  echo "-1"
}

# Get remaining minutes until reset from API
get_remaining_minutes() {
  local json="$1"

  if [ -z "$json" ]; then
    echo "0"
    return
  fi

  local resets_at
  resets_at=$(echo "$json" | jq -r '.five_hour.resets_at // empty' 2>/dev/null)

  if [ -n "$resets_at" ] && [ "$resets_at" != "null" ]; then
    # Calculate minutes until reset
    local reset_epoch now_epoch diff_seconds

    # Try macOS date format first, then GNU date
    reset_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${resets_at%%.*}" "+%s" 2>/dev/null || \
                  date -d "${resets_at}" "+%s" 2>/dev/null || echo "0")
    now_epoch=$(date "+%s")
    diff_seconds=$((reset_epoch - now_epoch))

    if [ "$diff_seconds" -gt 0 ]; then
      echo $((diff_seconds / 60))
      return
    fi
  fi

  echo "0"
}

# Check if we should continue based on usage
should_continue() {
  local json="$1"

  # Check usage percentage
  if [ "$MAX_USAGE_PERCENT" -gt 0 ] 2>/dev/null; then
    local usage_percent
    usage_percent=$(get_usage_percent "$json")
    if [ "$usage_percent" = "-1" ]; then
      log "Warning: Could not get usage from Claude Code API. Make sure you're logged in (claude /login)."
    else
      local exceeded
      exceeded=$(echo "$usage_percent >= $MAX_USAGE_PERCENT" | bc 2>/dev/null || echo "0")
      if [ "$exceeded" = "1" ]; then
        log "Usage limit reached: ${usage_percent}% >= ${MAX_USAGE_PERCENT}%"
        return 1
      fi
    fi
  fi

  return 0
}

# Check if we should wait for new block
should_wait() {
  local json="$1"
  local usage_percent
  usage_percent=$(get_usage_percent "$json")

  # If we can't get usage, don't wait
  if [ "$usage_percent" = "-1" ]; then
    return 1
  fi

  local exceeded
  exceeded=$(echo "$usage_percent >= $WAIT_THRESHOLD" | bc 2>/dev/null || echo "0")
  [ "$exceeded" = "1" ]
}

# Wait for next block
wait_for_next_block() {
  local json="$1"
  local remaining_minutes
  remaining_minutes=$(get_remaining_minutes "$json")

  if [ "$remaining_minutes" -le 0 ]; then
    remaining_minutes=5
  fi

  log_status "Waiting for next usage block"
  log "Current block ends in approximately $remaining_minutes minutes"
  log "Will check every $CHECK_INTERVAL seconds..."

  while true; do
    local new_json
    new_json=$(get_usage_data)

    if ! should_wait "$new_json"; then
      log "Usage is now available! Continuing..."
      return 0
    fi

    local new_remaining
    new_remaining=$(get_remaining_minutes "$new_json")
    log "$(date '+%H:%M:%S') - Still waiting... (~${new_remaining}m remaining in block)"

    sleep "$CHECK_INTERVAL"
  done
}

# Display current usage status
show_status() {
  local json="$1"
  local usage_percent
  usage_percent=$(get_usage_percent "$json")
  local weekly_percent
  weekly_percent=$(get_weekly_percent "$json")
  local remaining
  remaining=$(get_remaining_minutes "$json")

  log ""
  log "Current Usage Status:"
  if [ "$usage_percent" = "-1" ]; then
    log "  5-hour:  N/A (not logged in - run 'claude /login')"
  else
    log "  5-hour:  ${usage_percent}%"
  fi
  if [ "$weekly_percent" != "-1" ]; then
    log "  7-day:   ${weekly_percent}%"
  fi
  if [ "$remaining" != "0" ]; then
    log "  Resets in: ${remaining}m"
  fi
  log ""
}

# Wait for next session (5-hour block)
wait_for_next_session() {
  local json="$1"
  local remaining_minutes
  remaining_minutes=$(get_remaining_minutes "$json")

  if [ "$remaining_minutes" -le 0 ]; then
    log "No active session or session just ended. Starting immediately..."
    return 0
  fi

  log_status "Waiting for next session"
  log "Current session ends in approximately $remaining_minutes minutes"
  log "Will start Ralph when the new session begins..."
  log "Press Ctrl+C to cancel"
  log ""

  # Wait until the session ends plus a small buffer
  local wait_seconds=$((remaining_minutes * 60 + 30))
  local end_time=$(($(date +%s) + wait_seconds))

  while [ "$(date +%s)" -lt "$end_time" ]; do
    local now=$(date +%s)
    local left=$((end_time - now))
    local mins=$((left / 60))
    local secs=$((left % 60))
    printf "\r  Time until next session: %02d:%02d " "$mins" "$secs"
    sleep 1
  done

  echo ""
  log ""
  log "New session starting now!"
  log ""
}

# Main execution
main() {
  check_dependencies

  log_status "Scheduled Ralph - Starting"
  log "Max iterations: $MAX_ITERATIONS"
  [ "$MAX_USAGE_PERCENT" -gt 0 ] 2>/dev/null && log "Max usage: ${MAX_USAGE_PERCENT}%"
  [ "$WAIT_NEXT_SESSION" = true ] && log "Wait for next session: enabled"
  [ "$WAIT_FOR_USAGE" = true ] && log "Wait during run: enabled (threshold: ${WAIT_THRESHOLD}%)"

  # Get initial usage
  local usage_json
  usage_json=$(get_usage_data)
  show_status "$usage_json"

  # Wait for next session if requested
  if [ "$WAIT_NEXT_SESSION" = true ]; then
    wait_for_next_session "$usage_json"
    usage_json=$(get_usage_data)
    show_status "$usage_json"
  fi

  # Check if we need to wait initially (due to high usage)
  if [ "$WAIT_FOR_USAGE" = true ] && should_wait "$usage_json"; then
    wait_for_next_block "$usage_json"
    usage_json=$(get_usage_data)
  fi

  # Check if we can start at all
  if ! should_continue "$usage_json"; then
    if [ "$WAIT_FOR_USAGE" = true ]; then
      wait_for_next_block "$usage_json"
    else
      log "Cannot start: usage limits already exceeded. Use --wait to wait for next block."
      exit 2
    fi
  fi

  if [ "$DRY_RUN" = true ]; then
    log ""
    log "[DRY RUN] Would run up to $MAX_ITERATIONS iterations"
    [ "$MAX_USAGE_PERCENT" -gt 0 ] 2>/dev/null && log "[DRY RUN] Would stop at ${MAX_USAGE_PERCENT}% usage"
    exit 0
  fi

  # Run the loop
  local iteration=0
  local PRD_FILE="$SCRIPT_DIR/prd.json"
  local PROGRESS_FILE="$SCRIPT_DIR/progress.txt"

  # Initialize progress file if needed
  if [ ! -f "$PROGRESS_FILE" ]; then
    echo "# Ralph Progress Log" > "$PROGRESS_FILE"
    echo "Started: $(date)" >> "$PROGRESS_FILE"
    echo "---" >> "$PROGRESS_FILE"
  fi

  for i in $(seq 1 "$MAX_ITERATIONS"); do
    # Re-check usage before each iteration
    usage_json=$(get_usage_data)

    if ! should_continue "$usage_json"; then
      if [ "$WAIT_FOR_USAGE" = true ]; then
        wait_for_next_block "$usage_json"
        usage_json=$(get_usage_data)
      else
        log_status "Stopping - Usage limit reached"
        show_status "$usage_json"
        log "Completed $iteration iterations before hitting limit."
        exit 0
      fi
    fi

    iteration=$i
    local usage_percent
    usage_percent=$(get_usage_percent "$usage_json")

    local usage_display="${usage_percent}%"
    [ "$usage_percent" = "-1" ] && usage_display="N/A"
    log_status "Ralph Iteration $i of $MAX_ITERATIONS (Usage: ${usage_display})"

    # Run claude code with the ralph prompt
    PROMPT_CONTENT=$(cat "$SCRIPT_DIR/prompt.md")
    OUTPUT=$(claude --print --dangerously-skip-permissions "$PROMPT_CONTENT" 2>&1 | tee /dev/stderr) || true

    # Check for completion signal
    if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
      log ""
      log "Ralph completed all tasks!"
      log "Completed at iteration $i of $MAX_ITERATIONS"
      exit 0
    fi

    log "Iteration $i complete. Continuing..."
    sleep 2
  done

  log ""
  log "Ralph reached max iterations ($MAX_ITERATIONS)."
  log "Check $PROGRESS_FILE for status."
  exit 1
}

main "$@"
