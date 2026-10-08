#!/bin/bash
# Runs the eight steps, then the checks. A few seconds on a laptop. No key, no account, no network.
set -e
cd "$(dirname "$0")"
for step in step1_call step2_tools step3_loop step4_meter step5_guard step6_cut step7_wire step8_price; do
  echo
  echo "=== $step.py"
  python3 $step.py
done
echo
python3 tests.py
