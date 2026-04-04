#!/usr/bin/env bash
set -euo pipefail

# Check that every .rs file in daemon/src/ is wired in its parent
# mod.rs/lib.rs/main.rs. Also checks router merge coverage and dead modules.
# Override: DAEMON_SRC=/path/to/src ./check-rust-wiring.sh
# Exit 0 = clean, Exit 1 = unwired files.

ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo '.')
SRC="${DAEMON_SRC:-$ROOT/daemon/src}"

[ ! -d "$SRC" ] && exit 0

UNWIRED=()

collect_declared_mods() {
  for pf in "$@"; do
    sed -E -n 's/.*mod[[:space:]]+([a-zA-Z_][a-zA-Z0-9_]*).*/\1/p' \
      "$pf" 2>/dev/null
  done | sort -u
}

collect_path_refs() {
  local dir="$1"
  {
    local -a files=()
    for f in "$dir"/*.rs; do [ -f "$f" ] && files+=("$f"); done
    if [ ${#files[@]} -gt 0 ]; then
      { grep -h '#\[path.*=.*"[^"]*"' "${files[@]}" 2>/dev/null || true; } \
        | sed -E -n 's/.*#\[path[[:space:]]*=[[:space:]]*"([^"]*)".*/\1/p' \
        | while read -r p; do basename "$p"; done
    fi
    { find "$dir" -mindepth 2 -name '*.rs' -print0 2>/dev/null \
      | xargs -0 grep -h '#\[path.*=.*"\.\./[^"]*"' 2>/dev/null || true; } \
      | sed -E -n 's/.*#\[path[[:space:]]*=[[:space:]]*"([^"]*)".*/\1/p' \
      | while read -r p; do
          case "$p" in ../*) basename "$p" ;; esac
        done
  } | sort -u
}

check_dir() {
  local dir="$1"; shift
  local -a parent_files=("$@")

  local -a declared=()
  while IFS= read -r m; do
    [ -n "$m" ] && declared+=("$m")
  done < <(collect_declared_mods "${parent_files[@]}")

  local -a path_refs=()
  while IFS= read -r p; do
    [ -n "$p" ] && path_refs+=("$p")
  done < <(collect_path_refs "$dir")

  for rs_file in "$dir"/*.rs; do
    [ -f "$rs_file" ] || continue
    local base; base=$(basename "$rs_file")
    case "$base" in mod.rs|lib.rs|main.rs) continue ;; esac
    case "$base" in *_tests.rs|*_test.rs|tests.rs) continue ;; esac

    local stem="${base%.rs}" found=false
    for d in "${declared[@]+"${declared[@]}"}"; do
      [ "$d" = "$stem" ] && { found=true; break; }
    done
    $found && continue
    for p in "${path_refs[@]+"${path_refs[@]}"}"; do
      [ "$p" = "$base" ] && { found=true; break; }
    done
    $found && continue
    UNWIRED+=("$rs_file")
  done
}

CHECKED_DIRS=""
while IFS= read -r parent_file; do
  dir=$(dirname "$parent_file")
  case ",$CHECKED_DIRS," in *",$dir,"*) continue ;; esac
  CHECKED_DIRS="${CHECKED_DIRS:+$CHECKED_DIRS,}$dir"

  local_parents=()
  for candidate in "$dir/mod.rs" "$dir/lib.rs" "$dir/main.rs"; do
    [ -f "$candidate" ] && local_parents+=("$candidate")
  done
  [ ${#local_parents[@]} -eq 0 ] && continue
  check_dir "$dir" "${local_parents[@]}"
done < <(find "$SRC" \( -name "mod.rs" -o -name "lib.rs" -o -name "main.rs" \) | sort)

if [ ${#UNWIRED[@]} -gt 0 ]; then
  echo "ERROR: ${#UNWIRED[@]} unwired .rs file(s):" >&2
  for f in "${UNWIRED[@]}"; do echo "  $f" >&2; done
  echo "Add 'mod <name>;' to the parent mod.rs/lib.rs" >&2
  exit 1
fi

# Router merge coverage check
check_router_merge() {
  local server_dir="$SRC/server"
  local routes_mod="$server_dir/routes/mod.rs"
  [ ! -d "$server_dir" ] || [ ! -f "$routes_mod" ] && return 0

  local warnings=0
  while IFS= read -r api_file; do
    [ -f "$api_file" ] || continue
    local stem; stem=$(basename "$api_file" .rs)
    if ! grep -q "${stem}::router()" "$routes_mod" 2>/dev/null; then
      echo "WARNING: router() in $api_file not merged in $routes_mod" >&2
      warnings=$((warnings + 1))
    fi
  done < <(grep -rl 'pub fn router()' "$server_dir"/api_*.rs 2>/dev/null || true)

  [ "$warnings" -gt 0 ] && echo "  $warnings router(s) unreachable." >&2
}
check_router_merge

# Dead module detection
check_dead_modules() {
  local warnings=0
  while IFS= read -r rs_file; do
    [ -f "$rs_file" ] || continue
    local base; base=$(basename "$rs_file")
    case "$base" in mod.rs|lib.rs|main.rs) continue ;; esac
    case "$base" in *_tests.rs|*_test.rs|tests.rs) continue ;; esac

    local stem="${base%.rs}"
    grep -q 'pub fn' "$rs_file" 2>/dev/null || continue

    local callers
    callers=$(find "$SRC" -name '*.rs' \
      ! -name '*_tests.rs' ! -name '*_test.rs' ! -name 'tests.rs' \
      ! -name 'mod.rs' ! -name 'lib.rs' ! -name 'main.rs' \
      ! -path "$rs_file" -print0 2>/dev/null \
      | xargs -0 grep -l "${stem}::" 2>/dev/null | wc -l || true)

    if [ "${callers:-0}" -eq 0 ]; then
      echo "WARNING: $rs_file has pub fn but no callers — potential dead code." >&2
      warnings=$((warnings + 1))
    fi
  done < <(find "$SRC" -name '*.rs' | sort)

  [ "$warnings" -gt 0 ] && echo "  $warnings module(s) unreferenced." >&2
}
check_dead_modules

exit 0
