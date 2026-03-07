#!/usr/bin/env bash
# first-boot.sh - SURVIVE OS first boot initialization
# This script runs once on initial startup via systemd

set -euo pipefail

MARKER="/var/lib/survive/.first-boot-complete"
LOG="/var/log/survive/first-boot.log"

# Exit if already completed
if [ -f "$MARKER" ]; then
    echo "First boot already completed, skipping."
    exit 0
fi

mkdir -p /var/log/survive
exec > >(tee -a "$LOG") 2>&1

echo "========================================"
echo "  SURVIVE OS - First Boot Setup"
echo "  $(date)"
echo "========================================"

# Generate SSH host keys
echo "[1/6] Generating SSH host keys..."
if [ ! -f /etc/ssh/ssh_host_ed25519_key ]; then
    ssh-keygen -A
    echo "  SSH keys generated."
else
    echo "  SSH keys already exist, skipping."
fi

# Initialize LLDAP with default admin
echo "[2/6] Initializing LLDAP directory..."
LLDAP_DIR="/var/lib/survive/lldap"
mkdir -p "$LLDAP_DIR"
chown survive:survive "$LLDAP_DIR"

# Generate a random admin password and store it
if [ ! -f "${LLDAP_DIR}/.admin-password" ]; then
    ADMIN_PASS=$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 16)
    echo "$ADMIN_PASS" > "${LLDAP_DIR}/.admin-password"
    chmod 600 "${LLDAP_DIR}/.admin-password"
    chown survive:survive "${LLDAP_DIR}/.admin-password"
    echo "  LLDAP admin password generated."

    # Update SSSD config with generated password
    if [ -f /etc/sssd/sssd.conf ]; then
        sed -i "s/ldap_default_authtok = changeme/ldap_default_authtok = ${ADMIN_PASS}/" \
            /etc/sssd/sssd.conf
    fi
fi

# Create SQLite databases for all modules
echo "[3/6] Creating module databases..."
MODULES=(platform identity comms security agriculture medical resources maps governance weather education)
for module in "${MODULES[@]}"; do
    DB_DIR="/var/lib/survive/${module}"
    DB_FILE="${DB_DIR}/${module}.db"
    mkdir -p "$DB_DIR"
    if [ ! -f "$DB_FILE" ]; then
        sqlite3 "$DB_FILE" "CREATE TABLE IF NOT EXISTS _meta (key TEXT PRIMARY KEY, value TEXT); INSERT OR IGNORE INTO _meta VALUES ('version', '1.0.0'), ('created', datetime('now'));"
        echo "  Created database: ${module}"
    fi
    chown -R survive:survive "$DB_DIR"
done

# Set up Redis
echo "[4/6] Configuring Redis..."
if [ -f /etc/redis/redis.conf ]; then
    # Bind to localhost only, disable persistence for pub/sub usage
    sed -i 's/^bind .*/bind 127.0.0.1/' /etc/redis/redis.conf
    sed -i 's/^# maxmemory .*/maxmemory 128mb/' /etc/redis/redis.conf
    echo "  Redis configured."
fi

# Configure WiFi AP if no wired network
echo "[5/6] Checking network..."
if ! ip route | grep -q default; then
    echo "  No default route detected. WiFi AP will be available."
    echo "  SSID: SURVIVE-NODE"
    echo "  Password: survive-setup"
    echo "  Web UI: http://10.42.0.1"
else
    echo "  Network connectivity detected."
fi

# Display setup information
echo "[6/6] Setup complete!"
echo ""
echo "========================================"
echo "  SURVIVE OS is ready!"
echo ""
echo "  Access the web interface:"
echo "    http://survive-node.local"
echo "    http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo '10.42.0.1')"
echo ""
echo "  Default login:"
echo "    Username: admin"
echo "    Password: $(cat /var/lib/survive/lldap/.admin-password 2>/dev/null || echo 'see /var/lib/survive/lldap/.admin-password')"
echo ""
echo "  Change the admin password immediately!"
echo "========================================"

# Mark first boot complete
touch "$MARKER"
chown survive:survive "$MARKER"
echo "First boot initialization completed at $(date)" >> "$MARKER"
