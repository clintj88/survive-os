# SURVIVE OS - MODULE_NAME

> Replace MODULE_NAME with your module name throughout this template.

## Overview

Brief description of what this module does.

## Setup

```bash
pip install -e ".[dev]"
```

## Running

```bash
uvicorn app:app --host 0.0.0.0 --port PORT
```

## Configuration

Config file: `/etc/survive/MODULE_NAME.yml`

## API

- `GET /health` - Health check returning `{status, version}`

## Data

Stored in `/var/lib/survive/MODULE_NAME/`
