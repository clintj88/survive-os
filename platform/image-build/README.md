# SURVIVE OS Image Builder

Build system for producing bootable SURVIVE OS images for ARM64 (Raspberry Pi 4) and x86_64 hardware, with an interactive module selector.

## Prerequisites

Install on Debian/Ubuntu:

```bash
# Primary tool (preferred)
sudo apt-get install debos

# Fallback (debootstrap)
sudo apt-get install debootstrap parted dosfstools e2fsprogs xz-utils

# For cross-architecture builds
sudo apt-get install qemu-user-static binfmt-support

# For interactive configurator (optional, falls back to text menu)
sudo apt-get install whiptail  # or: dialog
```

## Quick Start

```bash
cd platform/image-build

# 1. Choose your modules (interactive menu)
make configure

# 2. Build the image
make build-arm64 VARIANT=custom    # Raspberry Pi 4
make build-amd64 VARIANT=custom    # x86_64 PC
```

## Module Configurator

Run `./configure.sh` to interactively select which modules to include in your image.

### Preset Profiles

Start from a profile, then customize:

| Profile | Description | Modules |
|---------|-------------|---------|
| **Minimal** | Core only — add modules later | platform, identity, sync, backup, frontend |
| **Homestead** | Small farm/homestead | agriculture, weather, inventory, tools, medical basics |
| **Community** | Full community hub | comms, governance, trade, medical, education |
| **Field Medical** | Medical-focused deployment | full medical suite + comms |
| **Full** | Everything installed | all 29 optional modules |

### Core Modules (always installed)

These cannot be deselected — they are required for SURVIVE OS to function:

| Module | Description |
|--------|-------------|
| **★ Platform Shell** | Main UI, nginx proxy, shared libraries |
| **★ Identity & Auth** | LLDAP, SSSD/PAM, RBAC |
| **★ Sync Engine** | CRDT replication via Automerge |
| **★ Backup System** | Automated daily backups |
| **★ Frontend Shell** | Preact+HTM sidebar UI |

### CLI Options

```bash
./configure.sh [options]

Options:
  --output <path>     Output file (default: config/selected-modules.yml)
  --profile <name>    Start with preset (minimal, homestead, community, field-medical, full)
  --no-tui            Use text menu instead of dialog/whiptail
```

### Non-Interactive

Generate a config from a profile without the menu:

```bash
./configure.sh --profile homestead --no-tui
```

## Build Variants

```bash
./build.sh --arch arm64|amd64 [options]

Options:
  --arch arm64|amd64          Target architecture (required)
  --output <path>             Output file path
  --variant minimal|full|custom  Build variant (default: minimal)
  --suite <suite>             Debian suite (default: bookworm)
  --mirror <url>              Debian mirror URL
```

| Variant | Description |
|---------|-------------|
| `minimal` | Core modules only (platform, identity, sync, backup, frontend) |
| `full` | All modules — complete SURVIVE OS |
| `custom` | Modules from `config/selected-modules.yml` (run `./configure.sh` first) |

### Make Targets

```bash
make help           # Show all targets
make configure      # Interactive module selector
make build-arm64    # Build ARM64 image
make build-amd64    # Build AMD64 image
make build-all      # Build both (parallel)
make checksums      # Generate SHA256 checksums
make clean          # Remove build artifacts
```

Pass variant: `make build-arm64 VARIANT=custom`

## Flashing Images

### Raspberry Pi 4 (ARM64)

```bash
xz -d output/survive-os-arm64.img.xz -c | sudo dd of=/dev/sdX bs=4M status=progress
```

### x86_64 PC / USB Drive

```bash
xz -d output/survive-os-amd64.img.xz -c | sudo dd of=/dev/sdX bs=4M status=progress
```

Replace `/dev/sdX` with your actual device (check with `lsblk`).

## First Boot

On first boot, SURVIVE OS will:

1. Generate SSH host keys
2. Initialize the LLDAP identity directory
3. Create SQLite databases for installed modules only
4. Configure Redis
5. Start WiFi AP if no wired network detected (SSID: `SURVIVE-NODE`, password: `survive-setup`)
6. Display the setup URL on console

Access the web UI at `http://survive-node.local` or `http://<ip-address>`.

## Output

```
output/
  survive-os-arm64.img.xz         # Compressed ARM64 image
  survive-os-arm64.img.xz.sha256  # Checksum
  survive-os-amd64.img.xz         # Compressed x86_64 image
  survive-os-amd64.img.xz.sha256  # Checksum
```

## Architecture

The build system uses **debos** for declarative image building, falling back to **debootstrap** for manual rootfs construction.

```
configure.sh          -> Interactive module selector (generates selected-modules.yml)
build.sh              -> Main build script (debootstrap/debos)
config/
  modules.yml         -> Module registry (IDs, deps, core flags, profiles)
  selected-modules.yml -> Generated module selection (from configure.sh)
  image-config.yml    -> Image settings (partitions, packages, variants)
scripts/
  install-modules.sh  -> Installs selected modules into rootfs
  first-boot.sh       -> First boot initialization (reads module manifest)
  configure-network.sh -> Network/firewall setup
```

### Partition Layouts

**ARM64 (Pi 4):** MBR, 256MB FAT32 boot + ext4 root (4GB total)

**AMD64 (x86_64):** GPT, 512MB EFI + ext4 root (8GB total)
