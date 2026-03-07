#!/usr/bin/env bash
# Install and configure SSSD on a Debian system for SURVIVE OS identity.
# Usage: sudo ./install-sssd.sh --host <lldap-host> --password <bind-password>
# Requires: root privileges, Debian-based system

set -euo pipefail

LLDAP_HOST="${LLDAP_HOST:-localhost}"
LLDAP_LDAP_PORT="${LLDAP_LDAP_PORT:-3890}"
LLDAP_LDAP_BASE_DN="${LLDAP_LDAP_BASE_DN:-dc=survive,dc=local}"
LLDAP_ADMIN_USERNAME="${LLDAP_ADMIN_USERNAME:-admin}"
LLDAP_ADMIN_PASSWORD="${LLDAP_ADMIN_PASSWORD:-}"

usage() {
    echo "Usage: sudo $0 --host <lldap-host> --password <bind-password>"
    echo ""
    echo "Options:"
    echo "  --host       LLDAP server hostname (default: localhost)"
    echo "  --port       LLDAP LDAP port (default: 3890)"
    echo "  --base-dn    LDAP base DN (default: dc=survive,dc=local)"
    echo "  --admin      Bind DN username (default: admin)"
    echo "  --password   Bind DN password (required)"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --host) LLDAP_HOST="$2"; shift 2 ;;
        --port) LLDAP_LDAP_PORT="$2"; shift 2 ;;
        --base-dn) LLDAP_LDAP_BASE_DN="$2"; shift 2 ;;
        --admin) LLDAP_ADMIN_USERNAME="$2"; shift 2 ;;
        --password) LLDAP_ADMIN_PASSWORD="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

if [ -z "$LLDAP_ADMIN_PASSWORD" ]; then
    echo "ERROR: --password is required." >&2
    usage
fi

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: This script must be run as root." >&2
    exit 1
fi

echo "Installing SSSD and dependencies..."
apt-get update -qq
apt-get install -y -qq sssd sssd-ldap libnss-sss libpam-sss

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Generating sssd.conf from template..."
sed -e "s|{{ LLDAP_HOST }}|${LLDAP_HOST}|g" \
    -e "s|{{ LLDAP_LDAP_PORT }}|${LLDAP_LDAP_PORT}|g" \
    -e "s|{{ LLDAP_LDAP_BASE_DN }}|${LLDAP_LDAP_BASE_DN}|g" \
    -e "s|{{ LLDAP_ADMIN_USERNAME }}|${LLDAP_ADMIN_USERNAME}|g" \
    -e "s|{{ LLDAP_ADMIN_PASSWORD }}|${LLDAP_ADMIN_PASSWORD}|g" \
    "${SCRIPT_DIR}/sssd.conf.template" > /etc/sssd/sssd.conf

chmod 600 /etc/sssd/sssd.conf
chown root:root /etc/sssd/sssd.conf

echo "Installing PAM configuration..."
cp "${SCRIPT_DIR}/pam.d-survive" /etc/pam.d/survive

echo "Updating nsswitch.conf..."
for db in passwd group shadow netgroup sudoers; do
    if grep -q "^${db}:" /etc/nsswitch.conf; then
        if ! grep -q "sss" /etc/nsswitch.conf | grep "^${db}:"; then
            sed -i "s/^${db}:.*/${db}:     files sss/" /etc/nsswitch.conf
        fi
    else
        echo "${db}:     files sss" >> /etc/nsswitch.conf
    fi
done

echo "Enabling and starting SSSD..."
systemctl enable sssd
systemctl restart sssd

echo "SSSD installation complete. Test with: id <username>"
