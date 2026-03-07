#!/usr/bin/env bash
# configure.sh - Interactive module selector for SURVIVE OS image builds
# Generates a module selection config consumed by build.sh --variant custom
#
# Usage: ./configure.sh [--output <path>] [--profile <name>] [--no-tui]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODULES_REGISTRY="${SCRIPT_DIR}/config/modules.yml"
OUTPUT="${SCRIPT_DIR}/config/selected-modules.yml"
PROFILE=""
NO_TUI=false

# Colors
BOLD='\033[1m'
DIM='\033[2m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
STAR='\033[1;33m★\033[0m'

usage() {
    cat << EOF
SURVIVE OS Module Configurator

Usage: $(basename "$0") [options]

Options:
  --output <path>     Output selection file (default: config/selected-modules.yml)
  --profile <name>    Start with a preset profile (minimal, homestead, community,
                      field-medical, full)
  --no-tui            Use simple text menu instead of dialog/whiptail
  -h, --help          Show this help

The configurator generates a module selection file used by:
  ./build.sh --arch arm64 --variant custom
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output) OUTPUT="$2"; shift 2 ;;
        --profile) PROFILE="$2"; shift 2 ;;
        --no-tui) NO_TUI=true; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

# ── YAML parser (lightweight, no python dependency needed at configure time) ──

# Parse modules from registry into bash arrays
declare -a MOD_IDS=()
declare -a MOD_NAMES=()
declare -a MOD_DESCS=()
declare -a MOD_CORE=()
declare -a MOD_CATEGORIES=()
declare -a MOD_DEPS=()
declare -a MOD_SUBMODS=()
declare -a MOD_SELECTED=()

parse_modules() {
    local in_modules=false
    local in_profiles=false
    local idx=-1
    local current_field=""
    local deps=""
    local submods=""

    while IFS= read -r line; do
        # Skip comments and blank lines
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// /}" ]] && continue

        if [[ "$line" == "modules:" ]]; then
            in_modules=true; in_profiles=false; continue
        fi
        if [[ "$line" == "profiles:" ]]; then
            in_modules=false; in_profiles=true; continue
        fi

        if $in_modules; then
            # New module entry
            if [[ "$line" =~ ^[[:space:]]*-[[:space:]]*id:[[:space:]]*(.*) ]]; then
                # Save previous module's deps/submods
                if (( idx >= 0 )); then
                    MOD_DEPS[$idx]="$deps"
                    MOD_SUBMODS[$idx]="$submods"
                fi
                idx=$((idx + 1))
                MOD_IDS[$idx]="${BASH_REMATCH[1]}"
                MOD_NAMES[$idx]=""
                MOD_DESCS[$idx]=""
                MOD_CORE[$idx]="false"
                MOD_CATEGORIES[$idx]=""
                MOD_SELECTED[$idx]="off"
                deps=""
                submods=""
                current_field=""
                continue
            fi

            (( idx < 0 )) && continue

            if [[ "$line" =~ ^[[:space:]]+name:[[:space:]]*\"(.*)\" ]]; then
                MOD_NAMES[$idx]="${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^[[:space:]]+description:[[:space:]]*\"(.*)\" ]]; then
                MOD_DESCS[$idx]="${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^[[:space:]]+core:[[:space:]]*(true|false) ]]; then
                MOD_CORE[$idx]="${BASH_REMATCH[1]}"
                if [[ "${BASH_REMATCH[1]}" == "true" ]]; then
                    MOD_SELECTED[$idx]="on"
                fi
            elif [[ "$line" =~ ^[[:space:]]+category:[[:space:]]*(.*) ]]; then
                MOD_CATEGORIES[$idx]="${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^[[:space:]]+depends_on: ]]; then
                current_field="deps"
                # Inline list: depends_on: [platform, identity]
                if [[ "$line" =~ \[(.*)\] ]]; then
                    deps="${BASH_REMATCH[1]// /}"
                    current_field=""
                fi
            elif [[ "$line" =~ ^[[:space:]]+sub_modules: ]]; then
                current_field="submods"
            elif [[ "$line" =~ ^[[:space:]]+-[[:space:]]+(.*) ]]; then
                local val="${BASH_REMATCH[1]}"
                if [[ "$current_field" == "deps" ]]; then
                    [[ -n "$deps" ]] && deps="${deps},"
                    deps="${deps}${val}"
                elif [[ "$current_field" == "submods" ]]; then
                    [[ -n "$submods" ]] && submods="${submods},"
                    submods="${submods}${val}"
                fi
            else
                # Reset field if we hit a non-list line
                if [[ ! "$line" =~ ^[[:space:]]+-[[:space:]] ]]; then
                    current_field=""
                fi
            fi
        fi
    done < "$MODULES_REGISTRY"

    # Save last module
    if (( idx >= 0 )); then
        MOD_DEPS[$idx]="$deps"
        MOD_SUBMODS[$idx]="$submods"
    fi
}

# Parse profile module lists
declare -A PROFILE_MODULES=()
declare -A PROFILE_NAMES=()
declare -A PROFILE_DESCS=()

parse_profiles() {
    local in_profiles=false
    local current_profile=""
    local current_field=""

    while IFS= read -r line; do
        [[ "$line" =~ ^[[:space:]]*# ]] && continue

        if [[ "$line" == "profiles:" ]]; then
            in_profiles=true; continue
        fi
        if [[ "$line" == "modules:" ]]; then
            in_profiles=false; continue
        fi

        if $in_profiles; then
            if [[ "$line" =~ ^[[:space:]]{2}([a-z_-]+): ]]; then
                current_profile="${BASH_REMATCH[1]}"
                PROFILE_MODULES[$current_profile]=""
                current_field=""
                continue
            fi

            [[ -z "$current_profile" ]] && continue

            if [[ "$line" =~ ^[[:space:]]+name:[[:space:]]*\"(.*)\" ]]; then
                PROFILE_NAMES[$current_profile]="${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^[[:space:]]+description:[[:space:]]*\"(.*)\" ]]; then
                PROFILE_DESCS[$current_profile]="${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^[[:space:]]+modules: ]]; then
                current_field="modules"
            elif [[ "$current_field" == "modules" && "$line" =~ ^[[:space:]]+-[[:space:]]+(.*) ]]; then
                local val="${BASH_REMATCH[1]}"
                local existing="${PROFILE_MODULES[$current_profile]}"
                [[ -n "$existing" ]] && existing="${existing},"
                PROFILE_MODULES[$current_profile]="${existing}${val}"
            elif [[ ! "$line" =~ ^[[:space:]]+- ]]; then
                current_field=""
            fi
        fi
    done < "$MODULES_REGISTRY"
}

# ── Selection helpers ──

select_module() {
    local id="$1"
    for i in "${!MOD_IDS[@]}"; do
        if [[ "${MOD_IDS[$i]}" == "$id" ]]; then
            MOD_SELECTED[$i]="on"
            return 0
        fi
    done
}

deselect_module() {
    local id="$1"
    for i in "${!MOD_IDS[@]}"; do
        if [[ "${MOD_IDS[$i]}" == "$id" && "${MOD_CORE[$i]}" != "true" ]]; then
            MOD_SELECTED[$i]="off"
            return 0
        fi
    done
}

is_selected() {
    local id="$1"
    for i in "${!MOD_IDS[@]}"; do
        if [[ "${MOD_IDS[$i]}" == "$id" ]]; then
            [[ "${MOD_SELECTED[$i]}" == "on" ]] && return 0
            return 1
        fi
    done
    return 1
}

# Auto-select dependencies for all selected modules
resolve_dependencies() {
    local changed=true
    while $changed; do
        changed=false
        for i in "${!MOD_IDS[@]}"; do
            if [[ "${MOD_SELECTED[$i]}" == "on" && -n "${MOD_DEPS[$i]}" ]]; then
                IFS=',' read -ra deps <<< "${MOD_DEPS[$i]}"
                for dep in "${deps[@]}"; do
                    if ! is_selected "$dep"; then
                        select_module "$dep"
                        changed=true
                    fi
                done
            fi
        done
    done
}

apply_profile() {
    local profile="$1"
    if [[ -z "${PROFILE_MODULES[$profile]+x}" ]]; then
        echo "Unknown profile: $profile"
        return 1
    fi

    # Reset non-core modules
    for i in "${!MOD_IDS[@]}"; do
        if [[ "${MOD_CORE[$i]}" != "true" ]]; then
            MOD_SELECTED[$i]="off"
        fi
    done

    # Select profile modules
    if [[ -n "${PROFILE_MODULES[$profile]}" ]]; then
        IFS=',' read -ra mods <<< "${PROFILE_MODULES[$profile]}"
        for mod in "${mods[@]}"; do
            select_module "$mod"
        done
    fi

    resolve_dependencies
}

# ── TUI with dialog/whiptail ──

find_tui_tool() {
    if command -v whiptail &>/dev/null; then
        echo "whiptail"
    elif command -v dialog &>/dev/null; then
        echo "dialog"
    else
        echo ""
    fi
}

run_tui_menu() {
    local tool
    tool=$(find_tui_tool)

    if [[ -z "$tool" || "$NO_TUI" == "true" ]]; then
        run_text_menu
        return
    fi

    local term_height term_width
    term_height=$(tput lines 2>/dev/null || echo 24)
    term_width=$(tput cols 2>/dev/null || echo 80)
    local box_h=$((term_height - 4))
    local box_w=$((term_width - 4))
    (( box_h > 40 )) && box_h=40
    (( box_w > 100 )) && box_w=100
    local list_h=$((box_h - 8))

    # ── Step 1: Profile selection ──
    local profile_args=()
    for p in minimal homestead community field-medical full; do
        local pname="${PROFILE_NAMES[$p]:-$p}"
        local pdesc="${PROFILE_DESCS[$p]:-}"
        profile_args+=("$p" "${pname}: ${pdesc}")
    done
    profile_args+=("custom" "Custom: Pick individual modules")

    local selected_profile
    selected_profile=$($tool --title "SURVIVE OS — Module Profile" \
        --menu "\nSelect a starting profile. You can customize after.\n\n★ Core modules (platform, identity, sync, backup, frontend) are always included." \
        $box_h $box_w $((list_h < 8 ? list_h : 8)) \
        "${profile_args[@]}" \
        3>&1 1>&2 2>&3) || { echo "Cancelled."; exit 1; }

    if [[ "$selected_profile" != "custom" ]]; then
        apply_profile "$selected_profile"
    fi

    # ── Step 2: Module checklist ──
    local checklist_args=()
    local prev_category=""

    for i in "${!MOD_IDS[@]}"; do
        local id="${MOD_IDS[$i]}"
        local name="${MOD_NAMES[$i]}"
        local desc="${MOD_DESCS[$i]}"
        local is_core="${MOD_CORE[$i]}"
        local selected="${MOD_SELECTED[$i]}"

        if [[ "$is_core" == "true" ]]; then
            name="★ ${name} [CORE]"
        fi

        checklist_args+=("$id" "$name — $desc" "$selected")
    done

    local result
    result=$($tool --title "SURVIVE OS — Select Modules" \
        --checklist "\n★ = Core (required, cannot be deselected)\nUse SPACE to toggle, ENTER to confirm.\n" \
        $box_h $box_w $list_h \
        "${checklist_args[@]}" \
        3>&1 1>&2 2>&3) || { echo "Cancelled."; exit 1; }

    # Apply selections
    for i in "${!MOD_IDS[@]}"; do
        if [[ "${MOD_CORE[$i]}" == "true" ]]; then
            MOD_SELECTED[$i]="on"
        else
            MOD_SELECTED[$i]="off"
        fi
    done

    for selected_id in $result; do
        # whiptail/dialog may quote the values
        selected_id="${selected_id//\"/}"
        select_module "$selected_id"
    done

    resolve_dependencies
}

# ── Fallback text menu ──

run_text_menu() {
    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║         SURVIVE OS — Module Configurator                ║${NC}"
    echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Profile selection
    echo -e "${BOLD}Select a starting profile:${NC}"
    echo ""
    local pi=1
    local profile_list=(minimal homestead community field-medical full custom)
    for p in "${profile_list[@]}"; do
        if [[ "$p" == "custom" ]]; then
            echo -e "  ${CYAN}${pi})${NC} Custom — Pick individual modules"
        else
            local pname="${PROFILE_NAMES[$p]:-$p}"
            local pdesc="${PROFILE_DESCS[$p]:-}"
            echo -e "  ${CYAN}${pi})${NC} ${pname} — ${pdesc}"
        fi
        pi=$((pi + 1))
    done
    echo ""
    read -rp "Choose profile [1-${#profile_list[@]}]: " choice

    local pidx=$((choice - 1))
    if (( pidx >= 0 && pidx < ${#profile_list[@]} )); then
        local selected_profile="${profile_list[$pidx]}"
        if [[ "$selected_profile" != "custom" ]]; then
            apply_profile "$selected_profile"
            echo -e "  ${GREEN}Applied profile: ${selected_profile}${NC}"
        fi
    fi

    # Module toggle
    echo ""
    echo -e "${BOLD}Toggle modules (enter number to toggle, ${GREEN}A${NC}${BOLD}=select all, ${RED}N${NC}${BOLD}=deselect all, ${CYAN}D${NC}${BOLD}=done):${NC}"
    echo ""

    while true; do
        local prev_cat=""
        for i in "${!MOD_IDS[@]}"; do
            local cat="${MOD_CATEGORIES[$i]}"
            if [[ -n "$cat" && "$cat" != "$prev_cat" ]]; then
                echo -e "\n  ${BOLD}── ${cat^} ──${NC}"
                prev_cat="$cat"
            elif [[ -z "$cat" && "$prev_cat" != "_core" ]]; then
                echo -e "\n  ${BOLD}── Core (always installed) ──${NC}"
                prev_cat="_core"
            fi

            local marker
            if [[ "${MOD_CORE[$i]}" == "true" ]]; then
                marker="${STAR}"
                echo -e "   ${DIM}$((i+1)))${NC} ${marker} ${MOD_NAMES[$i]} ${DIM}[CORE]${NC}"
            elif [[ "${MOD_SELECTED[$i]}" == "on" ]]; then
                marker="${GREEN}[✓]${NC}"
                echo -e "   ${CYAN}$((i+1)))${NC} ${marker} ${MOD_NAMES[$i]}"
            else
                marker="${DIM}[ ]${NC}"
                echo -e "   ${CYAN}$((i+1)))${NC} ${marker} ${MOD_NAMES[$i]}"
            fi
        done

        echo ""
        read -rp "Toggle [1-${#MOD_IDS[@]}], A=all, N=none, D=done: " input

        case "$input" in
            [Dd]) break ;;
            [Aa])
                for i in "${!MOD_IDS[@]}"; do MOD_SELECTED[$i]="on"; done
                ;;
            [Nn])
                for i in "${!MOD_IDS[@]}"; do
                    [[ "${MOD_CORE[$i]}" == "true" ]] && continue
                    MOD_SELECTED[$i]="off"
                done
                ;;
            *)
                if [[ "$input" =~ ^[0-9]+$ ]]; then
                    local idx=$((input - 1))
                    if (( idx >= 0 && idx < ${#MOD_IDS[@]} )); then
                        if [[ "${MOD_CORE[$idx]}" == "true" ]]; then
                            echo -e "  ${YELLOW}Core modules cannot be deselected.${NC}"
                        elif [[ "${MOD_SELECTED[$idx]}" == "on" ]]; then
                            MOD_SELECTED[$idx]="off"
                        else
                            MOD_SELECTED[$idx]="on"
                        fi
                    fi
                fi
                ;;
        esac

        resolve_dependencies
        # Clear screen for redraw
        printf '\033[2J\033[H'
        echo -e "${BOLD}Toggle modules (enter number to toggle, ${GREEN}A${NC}${BOLD}=all, ${RED}N${NC}${BOLD}=none, ${CYAN}D${NC}${BOLD}=done):${NC}"
    done

    resolve_dependencies
}

# ── Output ──

write_selection() {
    local selected_count=0
    local core_count=0

    {
        echo "# SURVIVE OS Module Selection"
        echo "# Generated by configure.sh on $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
        echo "#"
        echo "# Use with: ./build.sh --arch arm64 --variant custom"
        echo ""
        echo "selected_modules:"
    } > "$OUTPUT"

    for i in "${!MOD_IDS[@]}"; do
        if [[ "${MOD_SELECTED[$i]}" == "on" ]]; then
            echo "  - ${MOD_IDS[$i]}" >> "$OUTPUT"
            selected_count=$((selected_count + 1))
            [[ "${MOD_CORE[$i]}" == "true" ]] && core_count=$((core_count + 1))
        fi
    done

    # Also write the sub_modules list for install-modules.sh
    {
        echo ""
        echo "# Resolved sub-module directories to install"
        echo "sub_module_dirs:"
    } >> "$OUTPUT"

    for i in "${!MOD_IDS[@]}"; do
        if [[ "${MOD_SELECTED[$i]}" == "on" && -n "${MOD_SUBMODS[$i]}" ]]; then
            IFS=',' read -ra subs <<< "${MOD_SUBMODS[$i]}"
            for sub in "${subs[@]}"; do
                echo "  - ${sub}" >> "$OUTPUT"
            done
        fi
    done

    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║  Module Selection Complete                          ║${NC}"
    echo -e "${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${GREEN}Selected:${NC} ${selected_count} modules (${core_count} core + $((selected_count - core_count)) optional)"
    echo ""

    echo -e "  ${BOLD}Core (always installed):${NC}"
    for i in "${!MOD_IDS[@]}"; do
        if [[ "${MOD_CORE[$i]}" == "true" ]]; then
            echo -e "    ${STAR} ${MOD_NAMES[$i]}"
        fi
    done

    local has_optional=false
    for i in "${!MOD_IDS[@]}"; do
        if [[ "${MOD_SELECTED[$i]}" == "on" && "${MOD_CORE[$i]}" != "true" ]]; then
            if ! $has_optional; then
                echo ""
                echo -e "  ${BOLD}Optional (selected):${NC}"
                has_optional=true
            fi
            echo -e "    ${GREEN}✓${NC} ${MOD_NAMES[$i]}"
        fi
    done

    echo ""
    echo -e "  Config saved to: ${CYAN}${OUTPUT}${NC}"
    echo ""
    echo -e "  Build with:"
    echo -e "    ${CYAN}./build.sh --arch arm64 --variant custom${NC}"
    echo -e "    ${CYAN}./build.sh --arch amd64 --variant custom${NC}"
    echo ""
}

# ── Main ──

parse_modules
parse_profiles

# Apply profile from CLI if specified
if [[ -n "$PROFILE" ]]; then
    if [[ "$PROFILE" == "custom" ]]; then
        : # No preset
    else
        apply_profile "$PROFILE"
    fi
    run_tui_menu
else
    run_tui_menu
fi

write_selection
