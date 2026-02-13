#!/bin/bash
# Monitor orchestrator progress for Phase 1A workers

echo "=== Phase 1A Orchestrator Monitor ==="
echo "Monitoring file: validation/semantic_analyzer.py"
echo "Monitoring file: tests/validation/test_semantic_analyzer.py"
echo ""

# Function to check file status
check_file() {
    local file=$1
    if [ -f "$file" ]; then
        local lines=$(wc -l < "$file" 2>/dev/null || echo "0")
        local size=$(ls -lh "$file" 2>/dev/null | awk '{print $5}')
        local modified=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$file" 2>/dev/null || echo "unknown")
        echo "✓ EXISTS: $file ($lines lines, $size, modified: $modified)"
    else
        echo "✗ MISSING: $file"
    fi
}

# Function to show last git changes
show_recent_changes() {
    echo ""
    echo "=== Recent Git Changes ==="
    git status --short validation/ tests/validation/ 2>/dev/null || echo "No changes detected"
}

# Function to count methods in semantic_analyzer
count_methods() {
    if [ -f "validation/semantic_analyzer.py" ]; then
        local methods=$(grep -c "def " validation/semantic_analyzer.py 2>/dev/null || echo "0")
        echo ""
        echo "=== semantic_analyzer.py Methods Count: $methods ==="
        grep "def " validation/semantic_analyzer.py 2>/dev/null | sed 's/^/  /'
    fi
}

# Function to count tests
count_tests() {
    if [ -f "tests/validation/test_semantic_analyzer.py" ]; then
        local tests=$(grep -c "def test_" tests/validation/test_semantic_analyzer.py 2>/dev/null || echo "0")
        local skips=$(grep -c "pytest.skip" tests/validation/test_semantic_analyzer.py 2>/dev/null || echo "0")
        echo ""
        echo "=== test_semantic_analyzer.py Tests: $tests (skips: $skips) ==="
        grep "def test_" tests/validation/test_semantic_analyzer.py 2>/dev/null | sed 's/^/  /'
    fi
}

# Main monitoring loop
while true; do
    clear
    echo "=== Phase 1A Orchestrator Monitor ==="
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    check_file "validation/semantic_analyzer.py"
    check_file "tests/validation/test_semantic_analyzer.py"

    count_methods
    count_tests
    show_recent_changes

    echo ""
    echo "Press Ctrl+C to stop monitoring"
    echo "Refreshing in 5 seconds..."

    sleep 5
done
