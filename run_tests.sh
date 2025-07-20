#!/bin/bash

# WebCrawlerAPI Python SDK Test Runner
# This script sets up a virtual environment and runs the test suite

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Virtual environment directory
VENV_DIR="venv"

echo -e "${BLUE}WebCrawlerAPI Python SDK Test Runner${NC}"
echo "======================================="

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
print_status "Using Python $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
print_status "Installing package dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt > /dev/null 2>&1
else
    print_warning "requirements.txt not found, installing from setup.py"
fi

print_status "Installing development dependencies..."
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt > /dev/null 2>&1
else
    print_error "requirements-dev.txt not found"
    exit 1
fi

# Install package in development mode
print_status "Installing package in development mode..."
pip install -e . > /dev/null 2>&1

# Parse command line arguments
VERBOSE=""
COVERAGE=""
SPECIFIC_TEST=""
HTML_COVERAGE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -c|--coverage)
            COVERAGE="--cov=webcrawlerapi"
            shift
            ;;
        --html-coverage)
            COVERAGE="--cov=webcrawlerapi --cov-report=html"
            HTML_COVERAGE="true"
            shift
            ;;
        -t|--test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose        Run tests with verbose output"
            echo "  -c, --coverage       Run tests with coverage report"
            echo "  --html-coverage      Run tests with HTML coverage report"
            echo "  -t, --test FILE      Run specific test file"
            echo "  -h, --help           Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                          # Run all tests"
            echo "  $0 -v                       # Run with verbose output"
            echo "  $0 -c                       # Run with coverage"
            echo "  $0 --html-coverage          # Run with HTML coverage report"
            echo "  $0 -t tests/test_client.py  # Run specific test file"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest"

if [ -n "$VERBOSE" ]; then
    PYTEST_CMD="$PYTEST_CMD $VERBOSE"
fi

if [ -n "$COVERAGE" ]; then
    PYTEST_CMD="$PYTEST_CMD $COVERAGE"
fi

if [ -n "$SPECIFIC_TEST" ]; then
    if [ ! -f "$SPECIFIC_TEST" ]; then
        print_error "Test file not found: $SPECIFIC_TEST"
        exit 1
    fi
    PYTEST_CMD="$PYTEST_CMD $SPECIFIC_TEST"
fi

# Run tests
print_status "Running tests..."
echo "Command: $PYTEST_CMD"
echo ""

if $PYTEST_CMD; then
    echo ""
    print_status "All tests passed! ✅"
    
    if [ "$HTML_COVERAGE" = "true" ]; then
        echo ""
        print_status "HTML coverage report generated in htmlcov/index.html"
        
        # Try to open coverage report in browser (optional)
        if command -v open &> /dev/null; then
            read -p "Open coverage report in browser? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                open htmlcov/index.html
            fi
        fi
    fi
else
    echo ""
    print_error "Some tests failed! ❌"
    exit 1
fi

# Deactivate virtual environment
deactivate

print_status "Test run completed successfully!"