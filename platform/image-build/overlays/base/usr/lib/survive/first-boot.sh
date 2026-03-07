#!/usr/bin/env bash
# Wrapper that calls the actual first-boot script
# This file is placed in the overlay; the full script is at scripts/first-boot.sh
exec /usr/lib/survive/scripts/first-boot.sh "$@"
