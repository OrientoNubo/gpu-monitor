#!/bin/bash
#
# GPU Monitor Cron Collection Script
#
# This script is designed to be run by cron every 5 minutes.
# It collects GPU/CPU data from configured servers and pushes to GitHub.
#
# Installation:
#   1. Copy this script to your desired location
#   2. Make it executable: chmod +x cron_collect.sh
#   3. Edit the REPO_DIR variable below
#   4. Add to crontab: crontab -e
#      */5 * * * * /path/to/cron_collect.sh >> /var/log/gpu-monitor.log 2>&1
#

set -e

# Configuration - EDIT THIS
REPO_DIR="${GPU_MONITOR_REPO:-$HOME/gpu-monitor}"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Change to repo directory
if [ ! -d "$REPO_DIR" ]; then
    log "ERROR: Repository directory not found: $REPO_DIR"
    exit 1
fi

cd "$REPO_DIR"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

log "Starting data collection..."

# Run collector
python -m collector.main --verbose

# Check if there are changes
if [ -n "$(git status --porcelain docs/data/)" ]; then
    log "Changes detected, committing..."

    # Configure git if needed (for cron environment)
    git config user.email "${GIT_EMAIL:-gpu-monitor@localhost}" 2>/dev/null || true
    git config user.name "${GIT_NAME:-GPU Monitor Bot}" 2>/dev/null || true

    # Commit and push
    git add docs/data/
    git commit -m "Update monitor data $(date -Iseconds)"

    # Push with retry
    for i in 1 2 3; do
        if git push origin main; then
            log "Successfully pushed to GitHub"
            break
        else
            log "Push failed, attempt $i/3"
            sleep 5
        fi
    done
else
    log "No changes detected"
fi

log "Done"
