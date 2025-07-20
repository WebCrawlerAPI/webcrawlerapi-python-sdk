#!/bin/bash

# Local CI validation script
# This script simulates what GitHub Actions will run

set -e  # Exit on any error

echo "🚀 Running CI validation locally..."
echo "=================================="

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run ./run_tests.sh first."
    exit 1
fi

echo "1️⃣ Running tests with coverage..."
pytest --cov=webcrawlerapi --cov-report=xml --cov-report=term-missing -v

echo ""
echo "2️⃣ Checking code formatting with Black..."
black --check --diff .

echo ""
echo "3️⃣ Checking import sorting with isort..."
isort --check-only --diff .

echo ""
echo "4️⃣ Running flake8 linting..."
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

echo ""
echo "5️⃣ Running mypy type checking..."
mypy webcrawlerapi --ignore-missing-imports || echo "⚠️  Type checking warnings (non-blocking)"

echo ""
echo "6️⃣ Building package..."
python -m build

echo ""
echo "7️⃣ Checking package..."
twine check dist/*

echo ""
echo "✅ All CI checks passed!"
echo "🎉 Ready for GitHub Actions!"