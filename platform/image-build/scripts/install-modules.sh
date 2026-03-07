#!/usr/bin/env bash
# install-modules.sh - Install SURVIVE OS modules into the image
# Usage: install-modules.sh <rootfs_path> <variant> <repo_root>

set -euo pipefail

ROOTFS="${1:?Usage: install-modules.sh <rootfs_path> <variant> <repo_root>}"
VARIANT="${2:-minimal}"
REPO_ROOT="${3:-$(cd "$(dirname "$0")/../../../" && pwd)}"

SURVIVE_LIB="${ROOTFS}/var/lib/survive"
SURVIVE_ETC="${ROOTFS}/etc/survive"
SURVIVE_BIN="${ROOTFS}/usr/lib/survive"
SYSTEMD_DIR="${ROOTFS}/etc/systemd/system"

echo "==> Installing SURVIVE OS modules (variant: ${VARIANT})"
echo "    Root filesystem: ${ROOTFS}"
echo "    Source repo: ${REPO_ROOT}"

# Modules to install based on variant
MINIMAL_MODULES=(platform identity)
FULL_MODULES=(platform identity comms security agriculture medical resources maps governance weather education)

if [ "$VARIANT" = "full" ]; then
    MODULES=("${FULL_MODULES[@]}")
else
    MODULES=("${MINIMAL_MODULES[@]}")
fi

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

# Install a single module
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

    # Install Python dependencies if requirements.txt or pyproject.toml exists
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
            cp "$cfg" "${SURVIVE_ETC}/" 2>/dev/null || true
        fi
    done

    # Enable systemd service
    if [ -f "${SYSTEMD_DIR}/survive-module@.service" ]; then
        ln -sf "survive-module@.service" \
            "${SYSTEMD_DIR}/multi-user.target.wants/survive-module@${module}.service" 2>/dev/null || true
    fi
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

# Main installation sequence
mkdir -p "${SYSTEMD_DIR}/multi-user.target.wants"

install_nginx
install_service_template

for module in "${MODULES[@]}"; do
    install_module "$module"
done

setup_lldap
setup_sssd

# Set ownership
chown -R 900:900 "${SURVIVE_LIB}" 2>/dev/null || true
chown -R 900:900 "${SURVIVE_ETC}" 2>/dev/null || true

echo "==> Module installation complete (${#MODULES[@]} modules)"
