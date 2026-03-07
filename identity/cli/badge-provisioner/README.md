# Badge Provisioner CLI

CLI tool for managing SURVIVE OS user identities in LLDAP.

## Installation

```bash
cd identity/cli/badge-provisioner
pip install -e .
```

## Configuration

Set environment variables:

```bash
export LLDAP_URL=http://localhost:17170
export LLDAP_ADMIN_USERNAME=admin
export LLDAP_ADMIN_PASSWORD=your-password
```

## Usage

```bash
# Create a user with auto-generated badge ID
badge-provisioner create \
    --username jdoe \
    --display-name "Jane Doe" \
    --email jane@survive.local \
    --role medic \
    --team medical

# List all users
badge-provisioner list

# Assign a role/group
badge-provisioner assign-role --username jdoe --group admin

# Deactivate a user
badge-provisioner deactivate --username jdoe
```
