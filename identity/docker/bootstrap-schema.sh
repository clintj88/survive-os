#!/usr/bin/env bash
# Bootstrap LLDAP with SURVIVE OS custom schema and default groups.
# Usage: ./bootstrap-schema.sh
# Requires: curl, jq
# Environment: LLDAP_URL, LLDAP_ADMIN_USERNAME, LLDAP_ADMIN_PASSWORD

set -euo pipefail

LLDAP_URL="${LLDAP_URL:-http://localhost:17170}"
LLDAP_ADMIN_USERNAME="${LLDAP_ADMIN_USERNAME:-admin}"
LLDAP_ADMIN_PASSWORD="${LLDAP_ADMIN_PASSWORD:-change-me-in-production}"

echo "Waiting for LLDAP to be ready..."
for i in $(seq 1 30); do
    if curl -sf "${LLDAP_URL}/health" >/dev/null 2>&1 || curl -sf "${LLDAP_URL}" >/dev/null 2>&1; then
        echo "LLDAP is ready."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: LLDAP did not become ready in time." >&2
        exit 1
    fi
    sleep 2
done

# Authenticate and get JWT token
TOKEN=$(curl -sf "${LLDAP_URL}/auth/simple/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${LLDAP_ADMIN_USERNAME}\",\"password\":\"${LLDAP_ADMIN_PASSWORD}\"}" \
    | jq -r '.token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "ERROR: Failed to authenticate with LLDAP." >&2
    exit 1
fi

AUTH="Authorization: Bearer ${TOKEN}"

gql() {
    curl -sf "${LLDAP_URL}/api/graphql" \
        -H "$AUTH" \
        -H "Content-Type: application/json" \
        -d "$1"
}

# Create custom attributes for SURVIVE OS user schema
echo "Creating custom user attributes..."
for attr in \
    '{"name":"role","attributeType":"String","isEditable":true,"isVisible":true,"isList":false}' \
    '{"name":"team","attributeType":"String","isEditable":true,"isVisible":true,"isList":false}' \
    '{"name":"badge_id","attributeType":"String","isEditable":true,"isVisible":true,"isList":false}' \
; do
    ATTR_NAME=$(echo "$attr" | jq -r '.name')
    QUERY=$(cat <<GRAPHQL
{"query":"mutation { createUserAttribute(name: \"${ATTR_NAME}\", attributeType: $(echo "$attr" | jq -r '.attributeType | ascii_upcase'), isEditable: $(echo "$attr" | jq -r '.isEditable'), isVisible: $(echo "$attr" | jq -r '.isVisible'), isList: $(echo "$attr" | jq -r '.isList')) { ok } }"}
GRAPHQL
)
    RESULT=$(gql "$QUERY" 2>/dev/null || true)
    echo "  Attribute '${ATTR_NAME}': done"
done

# Create default groups
echo "Creating default groups..."
for group in admin medic farmer engineer security comms governance educator; do
    QUERY="{\"query\":\"mutation { createGroup(name: \\\"${group}\\\") { id displayName } }\"}"
    gql "$QUERY" >/dev/null 2>&1 || true
    echo "  Group '${group}': done"
done

echo "Schema bootstrap complete."
