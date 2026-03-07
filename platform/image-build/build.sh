#!/usr/bin/env bash
# build.sh - SURVIVE OS Image Builder
# Builds bootable Debian-based images for ARM64 (Raspberry Pi 4) and x86_64
#
# Usage: ./build.sh --arch arm64|amd64 [--output <path>] [--variant minimal|full]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
OUTPUT_DIR="${SCRIPT_DIR}/output"
RECIPES_DIR="${SCRIPT_DIR}/recipes"

# Defaults
ARCH=""
VARIANT="minimal"
OUTPUT=""
SUITE="bookworm"
MIRROR="http://deb.debian.org/debian"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    cat << EOF
SURVIVE OS Image Builder

Usage: $(basename "$0") --arch <arch> [options]

Options:
  --arch arm64|amd64    Target architecture (required)
  --output <path>       Output file path (default: output/survive-os-<arch>.img.xz)
  --variant minimal|full  Build variant (default: minimal)
                          minimal: base OS + identity + platform shell
                          full: all SURVIVE OS modules
  --suite <suite>       Debian suite (default: bookworm)
  --mirror <url>        Debian mirror URL
  -h, --help            Show this help

Examples:
  $(basename "$0") --arch arm64
  $(basename "$0") --arch amd64 --variant full --output my-image.img.xz
EOF
    exit 0
}

log() { echo -e "${GREEN}[BUILD]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --arch) ARCH="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        --variant) VARIANT="$2"; shift 2 ;;
        --suite) SUITE="$2"; shift 2 ;;
        --mirror) MIRROR="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) error "Unknown option: $1" ;;
    esac
done

# Validate
[[ -z "$ARCH" ]] && error "Architecture required. Use --arch arm64 or --arch amd64"
[[ "$ARCH" != "arm64" && "$ARCH" != "amd64" ]] && error "Architecture must be arm64 or amd64"
[[ "$VARIANT" != "minimal" && "$VARIANT" != "full" ]] && error "Variant must be minimal or full"

IMAGE_NAME="survive-os-${ARCH}.img"
[[ -z "$OUTPUT" ]] && OUTPUT="${OUTPUT_DIR}/${IMAGE_NAME}.xz"

# Estimated sizes
if [ "$ARCH" = "arm64" ]; then
    IMAGE_SIZE="4GB"
    log "Target: Raspberry Pi 4 (ARM64), image size: ${IMAGE_SIZE}"
else
    IMAGE_SIZE="8GB"
    log "Target: x86_64 (AMD64), image size: ${IMAGE_SIZE}"
fi
log "Variant: ${VARIANT}"
log "Output: ${OUTPUT}"

# Check for root
if [ "$(id -u)" -ne 0 ]; then
    error "This script must be run as root (image building requires root for loopback mounts)"
fi

# Check for cross-arch support
check_cross_arch() {
    local host_arch
    host_arch=$(dpkg --print-architecture 2>/dev/null || uname -m)

    # Normalize
    case "$host_arch" in
        x86_64|amd64) host_arch="amd64" ;;
        aarch64|arm64) host_arch="arm64" ;;
    esac

    if [ "$host_arch" != "$ARCH" ]; then
        log "Cross-architecture build detected (host: ${host_arch}, target: ${ARCH})"
        if ! command -v qemu-aarch64-static &>/dev/null && ! command -v qemu-x86_64-static &>/dev/null; then
            warn "qemu-user-static not found. Installing..."
            apt-get update && apt-get install -y qemu-user-static binfmt-support
        fi
        log "QEMU user-static available for cross-arch build"
    fi
}

# Build with debos
build_with_debos() {
    log "Building with debos..."

    if ! command -v debos &>/dev/null; then
        return 1
    fi

    mkdir -p "${OUTPUT_DIR}"

    debos \
        --artifactdir="${OUTPUT_DIR}" \
        --template-var="suite:${SUITE}" \
        --template-var="mirror:${MIRROR}" \
        --template-var="image:${IMAGE_NAME}" \
        "${RECIPES_DIR}/${ARCH}.yaml"

    return 0
}

# Build with debootstrap (fallback)
build_with_debootstrap() {
    log "Building with debootstrap (fallback mode)..."

    if ! command -v debootstrap &>/dev/null; then
        error "Neither debos nor debootstrap found. Install one of them:
  apt-get install debos    (preferred)
  apt-get install debootstrap"
    fi

    mkdir -p "${BUILD_DIR}" "${OUTPUT_DIR}"
    local rootfs="${BUILD_DIR}/rootfs"
    local img="${OUTPUT_DIR}/${IMAGE_NAME}"

    # Read package lists
    read_packages() {
        local file="$1"
        grep -v '^#' "$file" | grep -v '^$' | tr '\n' ',' | sed 's/,$//'
    }

    local base_pkgs
    base_pkgs=$(read_packages "${SCRIPT_DIR}/config/packages-base.list")
    local arch_pkgs
    arch_pkgs=$(read_packages "${SCRIPT_DIR}/config/packages-${ARCH}.list")

    # Debootstrap
    log "Running debootstrap for ${ARCH}..."
    local debootstrap_args=""
    if [ "$ARCH" = "arm64" ]; then
        debootstrap_args="--arch=arm64 --foreign"
    fi

    debootstrap ${debootstrap_args} \
        --components=main,contrib,non-free,non-free-firmware \
        --include="${base_pkgs}" \
        "${SUITE}" "${rootfs}" "${MIRROR}"

    # Complete foreign debootstrap if needed
    if [ "$ARCH" = "arm64" ] && [ "$(dpkg --print-architecture 2>/dev/null)" != "arm64" ]; then
        cp /usr/bin/qemu-aarch64-static "${rootfs}/usr/bin/" 2>/dev/null || true
        chroot "${rootfs}" /debootstrap/debootstrap --second-stage
    fi

    # Install arch-specific packages
    log "Installing architecture-specific packages..."
    chroot "${rootfs}" apt-get update
    chroot "${rootfs}" apt-get install -y --no-install-recommends \
        $(echo "$arch_pkgs" | tr ',' ' ')

    # Create survive user
    log "Creating survive user..."
    chroot "${rootfs}" groupadd --gid 900 survive 2>/dev/null || true
    chroot "${rootfs}" useradd --uid 900 --gid 900 --system \
        --create-home --shell /bin/bash survive 2>/dev/null || true
    chroot "${rootfs}" usermod -aG sudo survive

    # Create directory structure
    log "Setting up SURVIVE OS directories..."
    mkdir -p "${rootfs}/var/lib/survive"
    mkdir -p "${rootfs}/etc/survive"
    mkdir -p "${rootfs}/usr/lib/survive/scripts"
    mkdir -p "${rootfs}/var/log/survive"

    # Apply overlay
    log "Applying filesystem overlay..."
    cp -r "${SCRIPT_DIR}/overlays/base/"* "${rootfs}/"

    # Copy first-boot script
    cp "${SCRIPT_DIR}/scripts/first-boot.sh" "${rootfs}/usr/lib/survive/scripts/"
    chmod +x "${rootfs}/usr/lib/survive/scripts/first-boot.sh"
    chmod +x "${rootfs}/usr/lib/survive/first-boot.sh"

    # Configure locale
    log "Configuring locale and timezone..."
    echo "en_US.UTF-8 UTF-8" > "${rootfs}/etc/locale.gen"
    chroot "${rootfs}" locale-gen
    echo "LANG=en_US.UTF-8" > "${rootfs}/etc/default/locale"
    chroot "${rootfs}" ln -sf /usr/share/zoneinfo/UTC /etc/localtime

    # Configure network
    log "Configuring network..."
    bash "${SCRIPT_DIR}/scripts/configure-network.sh" "${rootfs}"

    # Install modules
    log "Installing SURVIVE OS modules..."
    bash "${SCRIPT_DIR}/scripts/install-modules.sh" "${rootfs}" "${VARIANT}" "${REPO_ROOT}"

    # Enable services
    log "Enabling services..."
    chroot "${rootfs}" systemctl enable systemd-networkd avahi-daemon \
        NetworkManager nginx redis-server ssh survive-first-boot.service 2>/dev/null || true

    # Configure sudo
    echo "survive ALL=(ALL) NOPASSWD: ALL" > "${rootfs}/etc/sudoers.d/survive"
    chmod 0440 "${rootfs}/etc/sudoers.d/survive"

    # Clean up
    chroot "${rootfs}" apt-get clean
    rm -rf "${rootfs}/var/lib/apt/lists/"*

    # Create disk image
    log "Creating disk image (${IMAGE_SIZE})..."
    local size_bytes
    size_bytes=$(numfmt --from=iec "${IMAGE_SIZE}" 2>/dev/null || echo 4294967296)
    truncate -s "${IMAGE_SIZE}" "${img}"

    if [ "$ARCH" = "arm64" ]; then
        # MBR partition table for Pi
        parted -s "${img}" mklabel msdos
        parted -s "${img}" mkpart primary fat32 1MiB 256MiB
        parted -s "${img}" set 1 boot on
        parted -s "${img}" mkpart primary ext4 256MiB 100%
    else
        # GPT for x86_64
        parted -s "${img}" mklabel gpt
        parted -s "${img}" mkpart efi fat32 1MiB 512MiB
        parted -s "${img}" set 1 boot on
        parted -s "${img}" set 1 esp on
        parted -s "${img}" mkpart root ext4 512MiB 100%
    fi

    # Set up loop device and format
    local loop
    loop=$(losetup --find --show --partscan "${img}")
    trap "losetup -d ${loop} 2>/dev/null || true" EXIT

    mkfs.vfat -n "SURVIVEBOOT" "${loop}p1"
    mkfs.ext4 -L "SURVIVEROOT" "${loop}p2"

    # Mount and copy
    local mnt="${BUILD_DIR}/mnt"
    mkdir -p "${mnt}"
    mount "${loop}p2" "${mnt}"
    mkdir -p "${mnt}/boot/firmware" "${mnt}/boot/efi"

    if [ "$ARCH" = "arm64" ]; then
        mount "${loop}p1" "${mnt}/boot/firmware"
    else
        mount "${loop}p1" "${mnt}/boot/efi"
    fi

    log "Copying filesystem to image..."
    cp -a "${rootfs}/"* "${mnt}/"

    # Install bootloader for amd64
    if [ "$ARCH" = "amd64" ]; then
        log "Installing GRUB bootloader..."
        chroot "${mnt}" grub-install --target=x86_64-efi \
            --efi-directory=/boot/efi --bootloader-id=survive \
            --no-nvram --removable 2>/dev/null || true
        chroot "${mnt}" update-grub 2>/dev/null || true
    fi

    # Unmount
    sync
    if [ "$ARCH" = "arm64" ]; then
        umount "${mnt}/boot/firmware"
    else
        umount "${mnt}/boot/efi"
    fi
    umount "${mnt}"
    losetup -d "${loop}"
    trap - EXIT

    log "Disk image created: ${img}"
}

# Compress image
compress_image() {
    local img="${OUTPUT_DIR}/${IMAGE_NAME}"
    if [ ! -f "$img" ]; then
        error "Image not found: ${img}"
    fi

    log "Compressing image with xz (this may take a while)..."
    xz -T0 -6 --force "${img}"

    local final="${img}.xz"
    if [ "$OUTPUT" != "$final" ]; then
        mv "$final" "$OUTPUT"
        final="$OUTPUT"
    fi

    local size
    size=$(du -h "$final" | cut -f1)
    local sha256
    sha256=$(sha256sum "$final" | cut -d' ' -f1)

    log "Build complete!"
    echo ""
    echo "  Image: ${final}"
    echo "  Size:  ${size}"
    echo "  SHA256: ${sha256}"
    echo ""
    echo "  Flash to SD card (ARM64):"
    echo "    xz -d ${final} -c | sudo dd of=/dev/sdX bs=4M status=progress"
    echo ""
    echo "  Flash to USB drive (AMD64):"
    echo "    xz -d ${final} -c | sudo dd of=/dev/sdX bs=4M status=progress"

    # Write checksum file
    echo "${sha256}  $(basename "$final")" > "${final}.sha256"
}

# Main
log "SURVIVE OS Image Builder"
log "========================"

check_cross_arch

if build_with_debos 2>/dev/null; then
    log "debos build successful"
else
    warn "debos not available or failed, falling back to debootstrap"
    build_with_debootstrap
fi

compress_image

log "Done!"
