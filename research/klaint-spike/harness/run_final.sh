#!/usr/bin/env bash
# KT-01 final evidence set on the changed fake provider (non-empty strings), Parlant v4.0.2.
cd REDACTED_HOME/AppData/Local/Temp/claude/kt01/parlant
export PYTHONPATH="REDACTED_HOME/w/kt01;$(pwd -W)"
PY=.venv/Scripts/python.exe; OUT=REDACTED_HOME/w/kt01/final; mkdir -p $OUT
$PY -m pytest tests/sdk/test_hook_results.py tests/core/stable/engines/test_hooks.py -c pytest.ini -q -p kt01_port -p no:cacheprovider -W ignore --rootdir=. -rA > $OUT/ported.log 2>&1; echo "ported EXIT=$?" >> $OUT/summary.txt
for t in smoke hooks security perf; do
  $PY -m pytest REDACTED_HOME/w/kt01/test_kt01_$t.py -c pytest.ini -q -s -p no:cacheprovider -W ignore --rootdir=. > $OUT/$t.log 2>&1; echo "$t EXIT=$?" >> $OUT/summary.txt
done
echo DONE >> $OUT/summary.txt
