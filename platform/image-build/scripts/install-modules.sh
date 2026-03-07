#!/usr/bin/env bash
# install-modules.sh - Install SURVIVE OS modules into the image
# Usage: install-modules.sh <rootfs_path> <variant> <repo_root>

set -euo pipefail

ROOTFS="${1:?Usage: install-modules.sh <rootfs_path> <variant> <repo_root>}"
VARIANT="${2:-minimal}"
REPO_ROOT="${3:-$(cd "$(dirname "$0")/../../../" && pwd)}"
IMAGE_BUILD_DIR="$(cd "$(dirname "$0")/.." && pwd)"

SURVIVE_LIB="${ROOTFS}/var/lib/survive"
SURVIVE_ETC="${ROOTFS}/etc/survive"
SURVIVE_BIN="${ROOTFS}/usr/lib/survive"
SYSTEMD_DIR="${ROOTFS}/etc/systemd/system"

echo "==> Installing SURVIVE OS modules (variant: ${VARIANT})"
echo "    Root filesystem: ${ROOTFS}"
echo "    Source repo: ${REPO_ROOT}"

# ── Resolve module list based on variant ──

MODULES=()

# Minimal: core platform dirs only
MINIMAL_DIRS=(
    platform/nginx
    platform/templates
    shared/db
    shared/blob
    sync
    platform/backup
    identity
    frontend
)

# Full: everything
FULL_DIRS=(
    platform/nginx
    platform/templates
    shared/db
    shared/blob
    sync
    platform/backup
    identity
    frontend
    comms/bbs
    comms/alerts
    comms/meshtastic-gw
    comms/ham-radio
    medical/ehr
    medical/concepts
    medical/lab
    medical/programs
    medical/pharmacy
    medical/epidemic
    medical/specialty
    agriculture/crop-planner
    agriculture/seed-bank
    agriculture/livestock
    agriculture/sensors
    security
    resources/inventory
    resources/tools
    resources/trade
    resources/energy
    resources/engineering
    maps/tile-server
    maps/annotations
    maps/drone-maps
    maps/print-maps
    governance
    weather
    education/knowledge-base
    education/learning
)

case "$VARIANT" in
    full)
        MODULES=("${FULL_DIRS[@]}")
        ;;
    custom)
        # Read sub_module_dirs from selected-modules.yml
        CUSTOM_CONFIG="${IMAGE_BUILD_DIR}/config/selected-modules.yml"
        if [ ! -f "$CUSTOM_CONFIG" ]; then
            echo "ERROR: Custom config not found: ${CUSTOM_CONFIG}"
            echo "Run ./configure.sh first."
            exit 1
        fi
        echo "    Custom config: ${CUSTOM_CONFIG}"
        # Parse the sub_module_dirs section
        local_in_section=false
        while IFS= read -r line; do
            if [[ "$line" == "sub_module_dirs:" ]]; then
                local_in_section=true
                continue
            fi
            if $local_in_section; then
                if [[ "$line" =~ ^[[:space:]]+-[[:space:]]+(.*) ]]; then
                    MODULES+=("${BASH_REMATCH[1]}")
                elif [[ ! "$line" =~ ^[[:space:]] ]]; then
                    break
                fi
            fi
        done < "$CUSTOM_CONFIG"
        ;;
    *)
        # minimal (default)
        MODULES=("${MINIMAL_DIRS[@]}")
        ;;
esac

echo "    Modules to install: ${#MODULES[@]}"

# ── Install functions ──

# Install nginx proxy config
install_nginx() {
    echo "  -> Installing nginx proxy configuration"
    local nginx_dir="${ROOTFS}/etc/nginx"
    mkdir -p "${nginx_dir}/sites-available" "${nginx_dir}/sites-enabled"

    if [ -f "${REPO_ROOT}/platform/nginx/survive-proxy.conf" ]; then
        cp "${REPO_ROOT}/platform/nginx/survive-proxy.conf" \
            "${nginx_dir}/sites-available/survive-proxy.conf"
        ln -sf ../sites-available/survive-proxy.conf \
            "${nginx_dir}/sites-enabled/survive-proxy.conf"
        rm -f "${nginx_dir}/sites-enabled/default"
    fi
}

# Install systemd service template
install_service_template() {
    echo "  -> Installing systemd service template"
    if [ -f "${REPO_ROOT}/platform/templates/survive-module.service" ]; then
        cp "${REPO_ROOT}/platform/templates/survive-module.service" \
            "${SYSTEMD_DIR}/survive-module@.service"
    fi
}

# Install a single module/sub-module
install_module() {
    local module="$1"
    local module_dir="${REPO_ROOT}/${module}"

    if [ ! -d "$module_dir" ]; then
        echo "  -> WARNING: Module directory not found: ${module_dir}, skipping"
        return 0
    fi

    echo "  -> Installing module: ${module}"

    # Create module data and config directories
    mkdir -p "${SURVIVE_LIB}/${module}"
    mkdir -p "${SURVIVE_ETC}"

    # Copy module files
    local dest="${SURVIVE_BIN}/modules/${module}"
    mkdir -p "${dest}"
    cp -r "${module_dir}/"* "${dest}/" 2>/dev/null || true

    # Remove __pycache__ from installed module
    find "${dest}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

    # Install Python dependencies if requirements.txt exists
    if [ -f "${module_dir}/requirements.txt" ]; then
        echo "     Installing Python dependencies for ${module}"
        chroot "${ROOTFS}" pip3 install --break-system-packages \
            -r "/usr/lib/survive/modules/${module}/requirements.txt" 2>/dev/null || \
        echo "     WARNING: Could not install Python deps for ${module} (chroot may not be available)"
    fi

    # Install Node dependencies if package.json exists
    if [ -f "${module_dir}/package.json" ]; then
        echo "     Installing Node dependencies for ${module}"
        chroot "${ROOTFS}" bash -c \
            "cd /usr/lib/survive/modules/${module} && npm install --production" 2>/dev/null || \
        echo "     WARNING: Could not install Node deps for ${module} (chroot may not be available)"
    fi

    # Copy config file if it exists
    for cfg in "${module_dir}"/*.yml "${module_dir}"/config/*.yml; do
        if [ -f "$cfg" ]; then
            local cfg_name
            cfg_name=$(basename "$cfg")
            # Don't copy module registry or test configs
            [[ "$cfg_name" == "modules.yml" ]] && continue
            [[ "$cfg_name" == "selected-modules.yml" ]] && continue
            [[ "$cfg_name" == "image-config.yml" ]] && continue
            cp "$cfg" "${SURVIVE_ETC}/" 2>/dev/null || true
        fi
    done

    # Install and enable dedicated systemd service if present
    for svc in "${module_dir}"/survive-*.service; do
        if [ -f "$svc" ]; then
            local svc_name
            svc_name=$(basename "$svc")
            cp "$svc" "${SYSTEMD_DIR}/${svc_name}"
            ln -sf "../${svc_name}" \
                "${SYSTEMD_DIR}/multi-user.target.wants/${svc_name}" 2>/dev/null || true
            echo "     Enabled service: ${svc_name}"
        fi
    done

    # Install systemd timers if present
    for timer in "${module_dir}"/survive-*.timer; do
        if [ -f "$timer" ]; then
            local timer_name
            timer_name=$(basename "$timer")
            cp "$timer" "${SYSTEMD_DIR}/${timer_name}"
            ln -sf "../${timer_name}" \
                "${SYSTEMD_DIR}/timers.target.wants/${timer_name}" 2>/dev/null || true
            echo "     Enabled timer: ${timer_name}"
        fi
    done
}

# Set up LLDAP
setup_lldap() {
    echo "  -> Configuring LLDAP directory service"
    local lldap_dir="${SURVIVE_LIB}/lldap"
    mkdir -p "${lldap_dir}"

    cat > "${SURVIVE_ETC}/lldap.yml" << 'EOF'
# LLDAP Configuration - initialized on first boot
ldap_port: 3890
http_port: 17170
ldap_base_dn: "dc=survive,dc=local"
database_url: "sqlite:///var/lib/survive/lldap/lldap.db"
EOF
}

# Set up SSSD for LDAP authentication
setup_sssd() {
    echo "  -> Configuring SSSD for LDAP authentication"
    local sssd_dir="${ROOTFS}/etc/sssd"
    mkdir -p "${sssd_dir}"

    cat > "${sssd_dir}/sssd.conf" << 'EOF'
[sssd]
services = nss, pam
config_file_version = 2
domains = survive

[domain/survive]
id_provider = ldap
auth_provider = ldap
ldap_uri = ldap://localhost:3890
ldap_search_base = dc=survive,dc=local
ldap_default_bind_dn = cn=admin,dc=survive,dc=local
ldap_default_authtok_type = password
ldap_default_authtok = changeme
cache_credentials = true
offline_credentials_expiration = 30
EOF

    chmod 600 "${sssd_dir}/sssd.conf"
}

# Write installed module manifest for first-boot and runtime use
write_manifest() {
    echo "  -> Writing module manifest"
    local manifest="${SURVIVE_ETC}/installed-modules.yml"
    {
        echo "# SURVIVE OS Installed Modules"
        echo "# Generated during image build on $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
        echo "variant: ${VARIANT}"
        echo "modules:"
        for module in "${MODULES[@]}"; do
            echo "  - ${module}"
        done
    } > "$manifest"
}

# ── Main installation sequence ──

mkdir -p "${SYSTEMD_DIR}/multi-user.target.wants"
mkdir -p "${SYSTEMD_DIR}/timers.target.wants"

install_nginx
install_service_template

for module in "${MODULES[@]}"; do
    install_module "$module"
done

setup_lldap
setup_sssd
write_manifest

# Set ownership
chown -R 900:900 "${SURVIVE_LIB}" 2>/dev/null || true
chown -R 900:900 "${SURVIVE_ETC}" 2>/dev/null || true

echo "==> Module installation complete (${#MODULES[@]} modules installed)"
