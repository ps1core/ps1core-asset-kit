#!/usr/bin/env bash
# End-to-end test of the kit's tools: build the buoy example, derive a 1942 soldier and a beyond ghoul, check them,
# draw their previews with maps and without (--flat), and make sure check.py rejects a broken entry.
#
#   tests/run.sh [--full] [--out DIR]
#
#   --full     also the shoggoth part (beyond shoggoth_a, 58k vertices): about 2 minutes more in the software preview
#   --out DIR  keep the submission and the preview sheets in DIR (default: a temporary folder, deleted at the end)
#
# Downloads the cast packages on first use (tools/fetch_cast.py: about 800 MB + 340 MB, cached). About 30 s after that.
set -euo pipefail
KIT=$(cd "$(dirname "$0")/.." && pwd); cd "$KIT"
FULL=0; OUT=
while [ $# -gt 0 ]; do case "$1" in --full) FULL=1;; --out) OUT=$2; shift;; *) sed -n 2,10p "$0"; exit 2;; esac; shift; done
if [ -z "$OUT" ]; then OUT=$(mktemp -d); trap 'rm -rf "$OUT"' EXIT; fi
mkdir -p "$OUT"; SUB=$OUT/sub; rm -rf "$SUB"
fail() { echo "FAIL: $*" >&2; exit 1; }
step() { echo "== $*"; }

step fetch the cast
python3 tools/fetch_cast.py >/dev/null
python3 tools/fetch_cast.py beyond >/dev/null

step build and derive
uv run -q examples/buoy/build.py "$SUB" >/dev/null
uv run -q tools/derive.py bf_ger_rifleman kit_example_diver "$SUB" --clips idle,walk,crouch,swim,crawl_up \
  --desc "a diver test, derived from the German rifleman, unchanged" >/dev/null
uv run -q tools/derive.py gh_m kit_example_ghoul "$SUB" --cast beyond --clips idle,walk,run,die \
  --desc "a ghoul test, derived from gh_m, unchanged" >/dev/null
MODELS="kit_buoy kit_example_diver kit_example_ghoul"
if [ "$FULL" = 1 ]; then
  uv run -q tools/derive.py shoggoth_a kit_example_shog "$SUB" --cast beyond \
    --desc "a shoggoth part test, derived from shoggoth_a, unchanged" >/dev/null
  MODELS="$MODELS kit_example_shog"
fi

step check
uv run -q tools/check.py "$SUB" > "$OUT/check.txt" || { cat "$OUT/check.txt"; fail "check.py found errors"; }
tail -1 "$OUT/check.txt"

step a broken entry must fail
python3 - "$SUB" <<'E'
import json, sys
p = sys.argv[1] + '/models.json'; c = json.load(open(p)); c['kit_buoy']['desc'] = 'TODO'; c['kit_buoy']['clips']['idle'][1] = 999
json.dump(c, open(p + '.bad', 'w'))
E
BAD=$OUT/bad; rm -rf "$BAD"; mkdir -p "$BAD"; cp -r "$SUB/progs" "$SUB/SOURCES.md" "$BAD/"; mv "$SUB/models.json.bad" "$BAD/models.json"
if uv run -q tools/check.py "$BAD" --model kit_buoy > "$OUT/check-bad.txt"; then fail "check.py passed a broken entry"; fi
grep -q "desc still says TODO" "$OUT/check-bad.txt" || fail "no TODO error"
grep -q "outside the model" "$OUT/check-bad.txt" || fail "no clip-range error"
echo "rejected, as it should be"

step preview
for m in $MODELS; do
  uv run -q tools/preview.py "$SUB" "$m" --out "$OUT/$m.png" >/dev/null || fail "preview $m"
  uv run -q tools/preview.py "$SUB" "$m" --flat --clips idle --out "$OUT/$m-flat.png" >/dev/null || fail "preview --flat $m"
  [ -s "$OUT/$m.png" ] && [ -s "$OUT/$m-flat.png" ] || fail "no sheet for $m"
  echo "$m ok"
done
[ "$FULL" = 1 ] || echo "skipped the shoggoth part (about 2 min): tests/run.sh --full"
echo "PASS"
