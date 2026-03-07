# SURVIVE OS Image Builder

Build system for producing bootable SURVIVE OS images for ARM64 (Raspberry Pi 4) and x86_64 hardware.

## Prerequisites

Install on Debian/Ubuntu:

```bash
# Primary tool (preferred)
sudo apt-get install debos

# Fallback (debootstrap)
sudo apt-get install debootstrap parted dosfstools e2fsprogs xz-utils

# For cross-architecture builds
sudo apt-get install qemu-user-static binfmt-support
```

## Usage

### Quick Start

```bash
# Build ARM64 image for Raspberry Pi 4
make build-arm64

# Build x86_64 image
make build-amd64

# Build both architectures in parallel
make build-all

# Build full variant (all modules)
make build-all VARIANT=full
```

### Build Script Options

```bash
./build.sh --arch arm64|amd64 [options]

Options:
  --arch arm64|amd64      Target architecture (required)
  --output <path>         Output file path
  --variant minimal|full  Build variant (default: minimal)
  --suite <suite>         Debian suite (default: bookworm)
  --mirror <url>          Debian mirror URL
```

### Build Variants

| Variant | Modules | Use Case |
|---------|---------|----------|
| `minimal` | platform, identity | Base node, add modules later |
| `full` | All 11 modules | Complete SURVIVE OS installation |

## Flashing Images

### Raspberry Pi 4 (ARM64)

```bash
# Decompress and write to SD card
xz -d output/survive-os-arm64.img.xz -c | sudo dd of=/dev/sdX bs=4M status=progress

# Verify
sudo sync
```

### x86_64 PC / USB Drive

```bash
# Decompress and write to USB drive
xz -d output/survive-os-amd64.img.xz -c | sudo dd of=/dev/sdX bs=4M status=progress

# Or use a tool like balenaEtcher with the .img.xz file directly
```

Replace `/dev/sdX` with your actual device (check with `lsblk`).

## First Boot

On first boot, SURVIVE OS will:

1. Generate SSH host keys
2. Initialize the LLDAP identity directory
3. Create SQLite databases for all modules
4. Configure Redis
5. Start WiFi AP if no wired network is detected (SSID: `SURVIVE-NODE`, password: `survive-setup`)
6. Display the setup URL on console

Access the web UI at `http://survive-node.local` or `http://<ip-address>`.

## Output

Built images are placed in `output/`:

```
output/
  survive-os-arm64.img.xz        # Compressed ARM64 image
  survive-os-arm64.img.xz.sha256  # Checksum
  survive-os-amd64.img.xz        # Compressed x86_64 image
  survive-os-amd64.img.xz.sha256  # Checksum
```

## Architecture

The build system uses **debos** (Debian OS builder) for declarative image building with YAML recipes, falling back to **debootstrap** for manual rootfs construction when debos is unavailable.

```
recipes/base.yaml   -> Common Debian base (packages, users, services)
recipes/arm64.yaml  -> Pi 4 kernel, firmware, boot config
recipes/amd64.yaml  -> x86 kernel, GRUB bootloader
```

### Partition Layouts

**ARM64 (Pi 4):** MBR, 256MB FAT32 boot + ext4 root (4GB total)

**AMD64 (x86_64):** GPT, 512MB EFI + ext4 root (8GB total)
