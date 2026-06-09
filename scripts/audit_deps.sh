#!/bin/bash
# EYTGaming Dependency Audit Script
# Runs pip-audit to check for known vulnerabilities in Python dependencies.
# Exit code is non-zero if any vulnerabilities are found.

set -euo pipefail

echo "=== EYTGaming Dependency Security Audit ==="
echo ""
echo "Running pip-audit on requirements.txt..."
echo ""

# Check if pip-audit is installed
if ! command -v pip-audit &> /dev/null; then
    echo "pip-audit not found. Installing..."
    pip install pip-audit
fi

# Run pip-audit with strict mode
pip-audit --requirement requirements.txt --strict

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ No vulnerabilities found! Dependencies are secure."
else
    echo ""
    echo "⚠️  Vulnerabilities found! Check the output above."
fi

exit $EXIT_CODE
