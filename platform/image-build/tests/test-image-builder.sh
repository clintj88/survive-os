#!/usr/bin/env bash
# test-image-builder.sh — Validate image builder configuration, scripts, and paths
# Runs without root, does not build an actual image.
#
# Usage: ./tests/test-image-builder.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
MODULES_REGISTRY="${SCRIPT_DIR}/config/modules.yml"

PASS=0
FAIL=0
TOTAL=0

# ── Test helpers ──

assert() {
    local desc="$1" result="$2"
    TOTAL=$((TOTAL + 1))
    if [[ "$result" == "true" ]]; then
        echo "  ✓ $desc"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $desc"
        FAIL=$((FAIL + 1))
    fi
}

assert_file_exists() {
    assert "File exists: $1" "$([[ -f "${SCRIPT_DIR}/$1" ]] && echo true || echo false)"
}

assert_dir_exists() {
    assert "Dir exists: $1" "$([[ -d "$1" ]] && echo true || echo false)"
}

assert_executable() {
    assert "Executable: $1" "$([[ -x "${SCRIPT_DIR}/$1" ]] && echo true || echo false)"
}

assert_syntax_ok() {
    local file="${SCRIPT_DIR}/$1"
    if bash -n "$file" 2>/dev/null; then
        assert "Syntax OK: $1" "true"
    else
        assert "Syntax OK: $1" "false"
    fi
}

# ── Module registry parser (subset of configure.sh) ──

declare -a MOD_IDS=() MOD_NAMES=() MOD_DESCS=() MOD_CORE=() MOD_CATEGORIES=()
declare -a MOD_DEPS=() MOD_SUBMODS=() MOD_SELECTED=() MOD_PORTS=()

parse_modules() {
    local in_modules=false in_profiles=false idx=-1 current_field="" deps="" submods=""
    while IFS= read -r line; do
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// /}" ]] && continue
        if [[ "$line" == "modules:" ]]; then in_modules=true; in_profiles=false; continue; fi
        if [[ "$line" == "profiles:" ]]; then
            in_modules=false; in_profiles=true
            if (( idx >= 0 )); then MOD_DEPS[$idx]="$deps"; MOD_SUBMODS[$idx]="$submods"; fi
            continue
        fi
        if $in_modules; then
            if [[ "$line" =~ ^[[:space:]]*-[[:space:]]*id:[[:space:]]*(.*) ]]; then
                if (( idx >= 0 )); then MOD_DEPS[$idx]="$deps"; MOD_SUBMODS[$idx]="$submods"; fi
                idx=$((idx + 1))
                MOD_IDS[$idx]="${BASH_REMATCH[1]}"; MOD_NAMES[$idx]=""; MOD_DESCS[$idx]=""
                MOD_CORE[$idx]="false"; MOD_CATEGORIES[$idx]=""; MOD_SELECTED[$idx]="off"
                MOD_PORTS[$idx]=""
                deps=""; submods=""; current_field=""
                continue
            fi
            (( idx < 0 )) && continue
            if [[ "$line" =~ ^[[:space:]]+name:[[:space:]]*\"(.*)\" ]]; then MOD_NAMES[$idx]="${BASH_REMATCH[1]}"; fi
            if [[ "$line" =~ ^[[:space:]]+description:[[:space:]]*\"(.*)\" ]]; then MOD_DESCS[$idx]="${BASH_REMATCH[1]}"; fi
            if [[ "$line" =~ ^[[:space:]]+core:[[:space:]]*(true|false) ]]; then
                MOD_CORE[$idx]="${BASH_REMATCH[1]}"
                [[ "${BASH_REMATCH[1]}" == "true" ]] && MOD_SELECTED[$idx]="on"
            fi
            if [[ "$line" =~ ^[[:space:]]+category:[[:space:]]*(.*) ]]; then MOD_CATEGORIES[$idx]="${BASH_REMATCH[1]}"; fi
            if [[ "$line" =~ ^[[:space:]]+port:[[:space:]]*(.*) ]]; then MOD_PORTS[$idx]="${BASH_REMATCH[1]}"; fi
            if [[ "$line" =~ ^[[:space:]]+depends_on: ]]; then
                current_field="deps"
                if [[ "$line" =~ \[(.*)\] ]]; then deps="${BASH_REMATCH[1]// /}"; current_field=""; fi
            elif [[ "$line" =~ ^[[:space:]]+sub_modules: ]]; then current_field="submods"
            elif [[ "$line" =~ ^[[:space:]]+-[[:space:]]+(.*) ]]; then
                local val="${BASH_REMATCH[1]}"
                if [[ "$current_field" == "deps" ]]; then [[ -n "$deps" ]] && deps="${deps},"; deps="${deps}${val}"
                elif [[ "$current_field" == "submods" ]]; then [[ -n "$submods" ]] && submods="${submods},"; submods="${submods}${val}"; fi
            else
                [[ ! "$line" =~ ^[[:space:]]+-[[:space:]] ]] && current_field=""
            fi
        fi
    done < "$MODULES_REGISTRY"
    if (( idx >= 0 )); then MOD_DEPS[$idx]="$deps"; MOD_SUBMODS[$idx]="$submods"; fi
}

# ── Dependency helpers ──

select_module() {
    for i in "${!MOD_IDS[@]}"; do
        [[ "${MOD_IDS[$i]}" == "$1" ]] && { MOD_SELECTED[$i]="on"; return 0; }
    done
}

deselect_all_optional() {
    for i in "${!MOD_IDS[@]}"; do
        [[ "${MOD_CORE[$i]}" == "true" ]] && MOD_SELECTED[$i]="on" || MOD_SELECTED[$i]="off"
    done
}

is_selected() {
    for i in "${!MOD_IDS[@]}"; do
        [[ "${MOD_IDS[$i]}" == "$1" ]] && { [[ "${MOD_SELECTED[$i]}" == "on" ]] && return 0; return 1; }
    done
    return 1
}

resolve_dependencies() {
    local changed=true
    while $changed; do
        changed=false
        for i in "${!MOD_IDS[@]}"; do
            if [[ "${MOD_SELECTED[$i]}" == "on" && -n "${MOD_DEPS[$i]}" ]]; then
                IFS=',' read -ra deps <<< "${MOD_DEPS[$i]}"
                for dep in "${deps[@]}"; do
                    if ! is_selected "$dep"; then select_module "$dep"; changed=true; fi
                done
            fi
        done
    done
}

# ── Parse profiles ──

declare -A PROFILE_MODULES=()
declare -A PROFILE_NAMES=()

parse_profiles() {
    local in_profiles=false current_profile="" current_field=""
    while IFS= read -r line; do
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        if [[ "$line" == "profiles:" ]]; then in_profiles=true; continue; fi
        if [[ "$line" == "modules:" ]]; then in_profiles=false; continue; fi
        if $in_profiles; then
            if [[ "$line" =~ ^[[:space:]]{2}([a-z_-]+): ]]; then
                current_profile="${BASH_REMATCH[1]}"; PROFILE_MODULES[$current_profile]=""; current_field=""
                continue
            fi
            [[ -z "$current_profile" ]] && continue
            if [[ "$line" =~ ^[[:space:]]+name:[[:space:]]*\"(.*)\" ]]; then PROFILE_NAMES[$current_profile]="${BASH_REMATCH[1]}"; fi
            if [[ "$line" =~ ^[[:space:]]+modules: ]]; then current_field="modules"; fi
            if [[ "$current_field" == "modules" && "$line" =~ ^[[:space:]]+-[[:space:]]+(.*) ]]; then
                local existing="${PROFILE_MODULES[$current_profile]}"
                [[ -n "$existing" ]] && existing="${existing},"
                PROFILE_MODULES[$current_profile]="${existing}${BASH_REMATCH[1]}"
            elif [[ ! "$line" =~ ^[[:space:]]+- ]]; then
                current_field=""
            fi
        fi
    done < "$MODULES_REGISTRY"
}

# ═══════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════"
echo "  SURVIVE OS Image Builder — Test Suite"
echo "═══════════════════════════════════════════════════"
echo ""

# ── 1. File structure ──
echo "── 1. File Structure ──"
assert_file_exists "build.sh"
assert_file_exists "configure.sh"
assert_file_exists "Makefile"
assert_file_exists "README.md"
assert_file_exists "config/modules.yml"
assert_file_exists "config/image-config.yml"
assert_file_exists "config/packages-base.list"
assert_file_exists "config/packages-amd64.list"
assert_file_exists "config/packages-arm64.list"
assert_file_exists "config/packages-modules.list"
assert_file_exists "scripts/install-modules.sh"
assert_file_exists "scripts/first-boot.sh"
assert_file_exists "scripts/configure-network.sh"
assert_file_exists "recipes/base.yaml"
assert_file_exists "arm64.yaml"
assert_file_exists "amd64.yaml"
assert_file_exists "overlays/base/etc/survive/platform.yml"
assert_file_exists "overlays/base/etc/systemd/system/survive-first-boot.service"
assert_file_exists "overlays/base/usr/lib/survive/first-boot.sh"

# ── 2. Script syntax ──
echo ""
echo "── 2. Shell Script Syntax ──"
assert_syntax_ok "build.sh"
assert_syntax_ok "configure.sh"
assert_syntax_ok "scripts/install-modules.sh"
assert_syntax_ok "scripts/first-boot.sh"
assert_syntax_ok "scripts/configure-network.sh"

# ── 3. Script permissions ──
echo ""
echo "── 3. Script Permissions ──"
assert_executable "build.sh"
assert_executable "configure.sh"

# ── 4. Module registry parsing ──
echo ""
echo "── 4. Module Registry Parsing ──"
parse_modules
assert "Parsed 34 modules total" "$([[ ${#MOD_IDS[@]} -eq 34 ]] && echo true || echo false)"

core_count=0
for i in "${!MOD_IDS[@]}"; do
    [[ "${MOD_CORE[$i]}" == "true" ]] && core_count=$((core_count + 1))
done
assert "Found 5 core modules" "$([[ $core_count -eq 5 ]] && echo true || echo false)"
assert "Found 29 optional modules" "$([[ $((${#MOD_IDS[@]} - core_count)) -eq 29 ]] && echo true || echo false)"

# ── 5. Core module IDs ──
echo ""
echo "── 5. Core Module Identification ──"
for core_id in platform identity sync backup frontend; do
    found=false
    for i in "${!MOD_IDS[@]}"; do
        [[ "${MOD_IDS[$i]}" == "$core_id" && "${MOD_CORE[$i]}" == "true" ]] && { found=true; break; }
    done
    assert "Core module: $core_id" "$found"
done

# ── 6. All modules have required fields ──
echo ""
echo "── 6. Module Metadata Completeness ──"
empty_names=0; empty_descs=0
for i in "${!MOD_IDS[@]}"; do
    [[ -z "${MOD_NAMES[$i]}" ]] && { echo "    MISSING name: ${MOD_IDS[$i]}"; empty_names=$((empty_names + 1)); }
    [[ -z "${MOD_DESCS[$i]}" ]] && { echo "    MISSING desc: ${MOD_IDS[$i]}"; empty_descs=$((empty_descs + 1)); }
done
assert "All modules have names" "$([[ $empty_names -eq 0 ]] && echo true || echo false)"
assert "All modules have descriptions" "$([[ $empty_descs -eq 0 ]] && echo true || echo false)"

# ── 7. No duplicate module IDs ──
echo ""
echo "── 7. Module ID Uniqueness ──"
dupes=$(printf '%s\n' "${MOD_IDS[@]}" | sort | uniq -d)
assert "No duplicate module IDs" "$([[ -z "$dupes" ]] && echo true || echo false)"
[[ -n "$dupes" ]] && echo "    Duplicates: $dupes"

# ── 8. No duplicate ports ──
echo ""
echo "── 8. Port Uniqueness ──"
declared_ports=()
for i in "${!MOD_IDS[@]}"; do
    [[ -n "${MOD_PORTS[$i]}" ]] && declared_ports+=("${MOD_PORTS[$i]}:${MOD_IDS[$i]}")
done
port_dupes=$(printf '%s\n' "${declared_ports[@]}" | cut -d: -f1 | sort | uniq -d)
assert "No duplicate port assignments" "$([[ -z "$port_dupes" ]] && echo true || echo false)"
if [[ -n "$port_dupes" ]]; then
    for p in $port_dupes; do
        owners=$(printf '%s\n' "${declared_ports[@]}" | grep "^${p}:" | cut -d: -f2 | tr '\n' ', ')
        echo "    Port $p claimed by: $owners"
    done
fi

# ── 9. Sub-module directories exist in repo ──
echo ""
echo "── 9. Sub-Module Directories Exist ──"
missing_dirs=()
for i in "${!MOD_IDS[@]}"; do
    if [[ -n "${MOD_SUBMODS[$i]}" ]]; then
        IFS=',' read -ra subs <<< "${MOD_SUBMODS[$i]}"
        for sub in "${subs[@]}"; do
            if [[ ! -d "${REPO_ROOT}/${sub}" ]]; then
                missing_dirs+=("${sub} (module: ${MOD_IDS[$i]})")
            fi
        done
    fi
done
assert "All sub-module directories exist" "$([[ ${#missing_dirs[@]} -eq 0 ]] && echo true || echo false)"
for m in "${missing_dirs[@]}"; do echo "    MISSING: $m"; done

# ── 10. Dependency targets exist ──
echo ""
echo "── 10. Dependency Targets Valid ──"
bad_deps=()
for i in "${!MOD_IDS[@]}"; do
    if [[ -n "${MOD_DEPS[$i]}" ]]; then
        IFS=',' read -ra deps <<< "${MOD_DEPS[$i]}"
        for dep in "${deps[@]}"; do
            found=false
            for j in "${!MOD_IDS[@]}"; do
                [[ "${MOD_IDS[$j]}" == "$dep" ]] && { found=true; break; }
            done
            $found || bad_deps+=("${MOD_IDS[$i]} depends on unknown: $dep")
        done
    fi
done
assert "All dependency targets are valid module IDs" "$([[ ${#bad_deps[@]} -eq 0 ]] && echo true || echo false)"
for b in "${bad_deps[@]}"; do echo "    BAD DEP: $b"; done

# ── 11. No circular dependencies ──
echo ""
echo "── 11. No Circular Dependencies ──"
circular=false
for i in "${!MOD_IDS[@]}"; do
    if [[ -n "${MOD_DEPS[$i]}" ]]; then
        IFS=',' read -ra deps <<< "${MOD_DEPS[$i]}"
        for dep in "${deps[@]}"; do
            # Check if dep depends back on us (direct cycle)
            for j in "${!MOD_IDS[@]}"; do
                if [[ "${MOD_IDS[$j]}" == "$dep" && -n "${MOD_DEPS[$j]}" ]]; then
                    IFS=',' read -ra dep_deps <<< "${MOD_DEPS[$j]}"
                    for dd in "${dep_deps[@]}"; do
                        if [[ "$dd" == "${MOD_IDS[$i]}" ]]; then
                            echo "    CYCLE: ${MOD_IDS[$i]} <-> $dep"
                            circular=true
                        fi
                    done
                fi
            done
        done
    fi
done
assert "No direct circular dependencies" "$([[ "$circular" == "false" ]] && echo true || echo false)"

# ── 12. Core modules are pre-selected ──
echo ""
echo "── 12. Core Module Default Selection ──"
for i in "${!MOD_IDS[@]}"; do
    if [[ "${MOD_CORE[$i]}" == "true" ]]; then
        assert "${MOD_IDS[$i]} is selected by default" "$([[ "${MOD_SELECTED[$i]}" == "on" ]] && echo true || echo false)"
    fi
done

# ── 13. Dependency resolution ──
echo ""
echo "── 13. Dependency Resolution ──"

# comms-alerts -> comms-bbs -> platform, identity
deselect_all_optional
select_module "comms-alerts"
resolve_dependencies
assert "comms-alerts pulls in comms-bbs" "$(is_selected comms-bbs && echo true || echo false)"
assert "comms-alerts pulls in identity" "$(is_selected identity && echo true || echo false)"

# maps-annotations -> maps-tiles -> platform
deselect_all_optional
select_module "maps-annotations"
resolve_dependencies
assert "maps-annotations pulls in maps-tiles" "$(is_selected maps-tiles && echo true || echo false)"

# medical-ehr -> medical-concepts -> platform, identity
deselect_all_optional
select_module "medical-ehr"
resolve_dependencies
assert "medical-ehr pulls in medical-concepts" "$(is_selected medical-concepts && echo true || echo false)"

# medical-lab -> medical-concepts
deselect_all_optional
select_module "medical-lab"
resolve_dependencies
assert "medical-lab pulls in medical-concepts" "$(is_selected medical-concepts && echo true || echo false)"

# ── 14. Profile parsing ──
echo ""
echo "── 14. Profile Parsing ──"
parse_profiles
assert "Profile: minimal exists" "$([[ -n "${PROFILE_NAMES[minimal]+x}" ]] && echo true || echo false)"
assert "Profile: homestead exists" "$([[ -n "${PROFILE_NAMES[homestead]+x}" ]] && echo true || echo false)"
assert "Profile: community exists" "$([[ -n "${PROFILE_NAMES[community]+x}" ]] && echo true || echo false)"
assert "Profile: field-medical exists" "$([[ -n "${PROFILE_NAMES[field-medical]+x}" ]] && echo true || echo false)"
assert "Profile: full exists" "$([[ -n "${PROFILE_NAMES[full]+x}" ]] && echo true || echo false)"

# ── 15. Profile module references valid ──
echo ""
echo "── 15. Profile Module References Valid ──"
bad_profile_refs=()
for profile in "${!PROFILE_MODULES[@]}"; do
    if [[ -n "${PROFILE_MODULES[$profile]}" ]]; then
        IFS=',' read -ra pmods <<< "${PROFILE_MODULES[$profile]}"
        for pmod in "${pmods[@]}"; do
            found=false
            for i in "${!MOD_IDS[@]}"; do
                [[ "${MOD_IDS[$i]}" == "$pmod" ]] && { found=true; break; }
            done
            $found || bad_profile_refs+=("Profile '$profile' references unknown module: $pmod")
        done
    fi
done
assert "All profile module references are valid" "$([[ ${#bad_profile_refs[@]} -eq 0 ]] && echo true || echo false)"
for b in "${bad_profile_refs[@]}"; do echo "    BAD REF: $b"; done

# ── 16. Debos recipe overlay path ──
echo ""
echo "── 16. Debos Recipe Paths ──"
# base.yaml uses a template variable for the overlay path
assert "base.yaml overlay uses template var" "$(grep -q 'overlay_base' "${SCRIPT_DIR}/recipes/base.yaml" && echo true || echo false)"
# build.sh passes the overlay_base template var to debos
assert "build.sh passes overlay_base to debos" "$(grep -q 'overlay_base' "${SCRIPT_DIR}/build.sh" && echo true || echo false)"
# The overlay directory itself exists
assert "overlays/base directory exists" "$([[ -d "${SCRIPT_DIR}/overlays/base" ]] && echo true || echo false)"

# ── 17. build.sh variant support ──
echo ""
echo "── 17. build.sh Variant Support ──"
assert "build.sh supports minimal" "$(grep -q 'minimal' "${SCRIPT_DIR}/build.sh" && echo true || echo false)"
assert "build.sh supports full" "$(grep -q '"full"' "${SCRIPT_DIR}/build.sh" && echo true || echo false)"
assert "build.sh supports custom" "$(grep -q '"custom"' "${SCRIPT_DIR}/build.sh" && echo true || echo false)"
assert "build.sh fails on debos error" "$(grep -q 'debos build failed' "${SCRIPT_DIR}/build.sh" && echo true || echo false)"

# ── 18. install-modules.sh handles all variants ──
echo ""
echo "── 18. install-modules.sh Variant Handling ──"
assert "Handles full variant" "$(grep -q 'full)' "${SCRIPT_DIR}/scripts/install-modules.sh" && echo true || echo false)"
assert "Handles custom variant" "$(grep -q 'custom)' "${SCRIPT_DIR}/scripts/install-modules.sh" && echo true || echo false)"
assert "Writes module manifest" "$(grep -q 'installed-modules.yml' "${SCRIPT_DIR}/scripts/install-modules.sh" && echo true || echo false)"

# ── 19. first-boot.sh reads manifest ──
echo ""
echo "── 19. first-boot.sh Manifest Integration ──"
assert "Reads installed-modules.yml" "$(grep -q 'installed-modules.yml' "${SCRIPT_DIR}/scripts/first-boot.sh" && echo true || echo false)"
assert "Has fallback for missing manifest" "$(grep -q 'No module manifest found' "${SCRIPT_DIR}/scripts/first-boot.sh" && echo true || echo false)"

# ── 20. Makefile targets ──
echo ""
echo "── 20. Makefile Targets ──"
assert "Has configure target" "$(grep -q '^configure:' "${SCRIPT_DIR}/Makefile" && echo true || echo false)"
assert "Has build-arm64 target" "$(grep -q '^build-arm64:' "${SCRIPT_DIR}/Makefile" && echo true || echo false)"
assert "Has build-amd64 target" "$(grep -q '^build-amd64:' "${SCRIPT_DIR}/Makefile" && echo true || echo false)"
assert "Has clean target" "$(grep -q '^clean:' "${SCRIPT_DIR}/Makefile" && echo true || echo false)"

# ── 21. Full install list covers all sub-modules ──
echo ""
echo "── 21. Full Variant Completeness ──"
# Every non-core module's sub_modules should appear in FULL_DIRS in install-modules.sh
install_script="${SCRIPT_DIR}/scripts/install-modules.sh"
missing_in_full=()
for i in "${!MOD_IDS[@]}"; do
    if [[ -n "${MOD_SUBMODS[$i]}" ]]; then
        IFS=',' read -ra subs <<< "${MOD_SUBMODS[$i]}"
        for sub in "${subs[@]}"; do
            if ! grep -q "$sub" "$install_script"; then
                missing_in_full+=("$sub (from ${MOD_IDS[$i]})")
            fi
        done
    fi
done
assert "All sub-modules listed in install-modules.sh FULL_DIRS" "$([[ ${#missing_in_full[@]} -eq 0 ]] && echo true || echo false)"
for m in "${missing_in_full[@]}"; do echo "    MISSING from FULL_DIRS: $m"; done

# ═══════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════"
if [[ $FAIL -eq 0 ]]; then
    echo "  ✓ ALL ${TOTAL} TESTS PASSED"
else
    echo "  ${PASS}/${TOTAL} passed, ${FAIL} FAILED"
fi
echo "═══════════════════════════════════════════════════"
echo ""

[[ $FAIL -eq 0 ]]
