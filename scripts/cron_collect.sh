#!/bin/bash
#
# GPU Monitor Cron Collection Script
#
# Crontab entry:
# */5 * * * * SSH_KEY_PASSPHRASE="your_passphrase" /path/to/cron_collect.sh >> /var/log/gpu-monitor.log 2>&1
#

set -e

# Configuration
REPO_DIR="/home/nubo/workspace/GPU_status_monitor_ssh"
SSH_KEY="$HOME/.ssh/id_ed25519"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Change to repo directory
cd "$REPO_DIR"

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

log "Starting data collection..."

# Run collector
python -m collector.main --verbose

# Check if there are changes
if [ -n "$(git status --porcelain docs/data/)" ]; then
    log "Changes detected, committing..."

    # Configure git
    git config user.email "gpu-monitor@localhost" 2>/dev/null || true
    git config user.name "GPU Monitor Bot" 2>/dev/null || true

    # Commit
    git add docs/data/
    git commit -m "Update monitor data $(date -Iseconds)"

    # Start ssh-agent and add key with passphrase
    eval "$(ssh-agent -s)" > /dev/null 2>&1

    # Use pexpect to handle passphrase
    if [ -n "$SSH_KEY_PASSPHRASE" ]; then
        python3 -c "
import pexpect
child = pexpect.spawn('ssh-add $SSH_KEY', timeout=30)
try:
    child.expect('passphrase')
    child.sendline('$SSH_KEY_PASSPHRASE')
    child.expect(pexpect.EOF)
except:
    pass
"
    fi

    # Push with retry
    for i in 1 2 3; do
        if git push origin main 2>&1; then
            log "Successfully pushed to GitHub"
            break
        else
            log "Push failed, attempt $i/3"
            sleep 5
        fi
    done

    # Kill ssh-agent
    ssh-agent -k > /dev/null 2>&1 || true
else
    log "No changes detected"
fi

log "Done"
