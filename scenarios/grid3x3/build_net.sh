#!/usr/bin/env bash
set -euo pipefail
# Generate 3x3 grid network for LaneRush. Run from project root.
# Verify flags with: netgenerate --help

OUTDIR="scenarios/grid3x3"
OUTFILE="${OUTDIR}/grid3x3.net.xml"

mkdir -p "${OUTDIR}"

netgenerate \
  --grid \
  --grid.number=3 \
  --grid.length=250 \
  --grid.attach-length=250 \
  --default.lanenumber=1 \
  --default.speed=13.89 \
  --default-junction-type=traffic_light \
  --tls.discard-simple=true \
  --output-file="${OUTFILE}"

echo "Network generated: ${OUTFILE}"
echo "TLS count: $(grep -c 'tlLogic' "${OUTFILE}" || echo 0)"
