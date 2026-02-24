#!/bin/bash
# test.sh - Quick test for annocli commands
# Tests commands: download, summary, stats, and alias
# Uses Honey Bee (taxid 7460) as test organism

set -e  # Exit on error 
set -o pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
SKIPPED=0

# Test directory
TEST_DIR="/tmp/annocli_test_$$"
TAXID=7460  # Honey Bee

# Helper functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_test() {
    echo -e "\n${BLUE}[TEST]${NC} $1"
}

pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    PASSED=$((PASSED + 1))
}

fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    echo -e "${RED}       $2${NC}"
    FAILED=$((FAILED + 1))
}

skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
    echo -e "${YELLOW}       $2${NC}"
    SKIPPED=$((SKIPPED + 1))
}

# Setup function
setup() {
    print_header "Setting up test environment"
    mkdir -p "$TEST_DIR"
    echo "Test directory: $TEST_DIR"
    echo "Test organism: Honey Bee (taxid $TAXID)"
}

# Cleanup function - only remove if tests passed
cleanup() {
    print_header "Cleaning up"
    if [ -d "$TEST_DIR" ]; then
        if [ $FAILED -eq 0 ]; then
            echo "Removing test directory: $TEST_DIR"
            rm -rf "$TEST_DIR"
            echo "Cleanup complete"
        else
            echo -e "${YELLOW}Test directory preserved for debugging: $TEST_DIR${NC}"
            echo -e "${YELLOW}Log files available:${NC}"
            find "$TEST_DIR" -name "*.log" 2>/dev/null | while read -r log; do
                echo "  - $log"
            done
        fi
    fi
}

# Test 1: Download command
test_download() {
    print_header "Testing DOWNLOAD command"
    
    # Test 1.1: Preview mode
    print_test "Download - Preview mode"
    if OUTPUT=$(annocli download $TAXID --mode prev 2>&1); then
        if echo "$OUTPUT" | grep -q "Taxids:" && echo "$OUTPUT" | grep -q "Annotations:"; then
            pass "Preview mode works correctly"
        else
            fail "Preview mode output format unexpected" "Expected 'Taxids:' and 'Annotations:' in output"
        fi
    else
        fail "Preview mode failed" "Command: annocli download $TAXID --mode prev"
    fi
    
    # Test 1.2: Links mode
    print_test "Download - Links mode"
    if OUTPUT=$(annocli download $TAXID --mode links --ref-only 2>&1); then
        if echo "$OUTPUT" | grep -q "wget" || echo "$OUTPUT" | grep -q "mkdir"; then
            pass "Links mode works correctly"
        else
            fail "Links mode output format unexpected" "Expected 'wget' or 'mkdir' commands in output"
        fi
    else
        fail "Links mode failed" "Command: annocli download $TAXID --mode links --ref-only"
    fi
    
    # Test 1.3: Actual download with assembly
    print_test "Download - Actual download with assembly"
    DOWNLOAD_DIR="$TEST_DIR/downloads"
    if annocli download $TAXID --ref-only --add-asm -o "$DOWNLOAD_DIR" 2>&1 | tee "$TEST_DIR/download.log"; then
        # Check if files were downloaded (check for both .gff.gz and .gff3.gz)
        GFF_FILES=$(find "$DOWNLOAD_DIR" \( -name "*.gff.gz" -o -name "*.gff3.gz" \) 2>/dev/null | wc -l)
        FNA_FILES=$(find "$DOWNLOAD_DIR" -name "*.fna.gz" 2>/dev/null | wc -l)
        
        if [ "$GFF_FILES" -gt 0 ] && [ "$FNA_FILES" -gt 0 ]; then
            pass "Download with assembly successful (GFF: $GFF_FILES, FNA: $FNA_FILES)"
            # Store paths for alias test (check both .gff.gz and .gff3.gz)
            export DOWNLOADED_GFF=$(find "$DOWNLOAD_DIR" \( -name "*.gff.gz" -o -name "*.gff3.gz" \) 2>/dev/null | head -1)
            export DOWNLOADED_FNA=$(find "$DOWNLOAD_DIR" -name "*.fna.gz" 2>/dev/null | head -1)
        else
            fail "Download incomplete" "Expected both GFF and FNA files (GFF: $GFF_FILES, FNA: $FNA_FILES)"
        fi
    else
        fail "Download command failed" "Check $TEST_DIR/download.log for details"
    fi
}

# Test 2: Summary command
test_summary() {
    print_header "Testing SUMMARY command"
    
    # Test 2.1: Basic summary
    print_test "Summary - Basic output"
    if OUTPUT=$(annocli summary $TAXID --ref-only 2>&1); then
        if echo "$OUTPUT" | grep -q -i "organism\|assembly\|taxid\|feature"; then
            pass "Summary basic output works correctly"
        else
            fail "Summary output format unexpected" "Expected organism/assembly/feature information"
        fi
    else
        fail "Summary command failed" "Command: annocli summary $TAXID --ref-only"
    fi
    
    # Test 2.2: TSV output
    print_test "Summary - TSV export"
    TSV_FILE="$TEST_DIR/summary.tsv"
    if annocli summary $TAXID --ref-only --tsv "$TSV_FILE" 2>&1 > /dev/null; then
        if [ -f "$TSV_FILE" ] && [ -s "$TSV_FILE" ]; then
            pass "Summary TSV export successful"
        else
            fail "Summary TSV file not created or empty" "Expected file: $TSV_FILE"
        fi
    else
        fail "Summary TSV export failed" "Command: annocli summary $TAXID --ref-only --tsv $TSV_FILE"
    fi
}

# Test 3: Stats command
test_stats() {
    print_header "Testing STATS command"
    
    # Test 3.1: Basic stats
    print_test "Stats - Basic output"
    if OUTPUT=$(annocli stats $TAXID --ref-only 2>&1); then
        # Stats output should contain some statistical information
        if [ -n "$OUTPUT" ]; then
            pass "Stats basic output works correctly"
        else
            fail "Stats output is empty" "Expected statistical information"
        fi
    else
        fail "Stats command failed" "Command: annocli stats $TAXID --ref-only"
    fi
    
    # Test 3.2: TSV output
    print_test "Stats - TSV export"
    TSV_FILE="$TEST_DIR/stats.tsv"
    if annocli stats $TAXID --ref-only --tsv "$TSV_FILE" 2>&1 > /dev/null; then
        if [ -f "$TSV_FILE" ] && [ -s "$TSV_FILE" ]; then
            pass "Stats TSV export successful"
        else
            fail "Stats TSV file not created or empty" "Expected file: $TSV_FILE"
        fi
    else
        fail "Stats TSV export failed" "Command: annocli stats $TAXID --ref-only --tsv $TSV_FILE"
    fi
}

# Test 4: Alias command
test_alias() {
    print_header "Testing ALIAS command"
    
    # Check if we have downloaded files from the download test
    if [ -z "$DOWNLOADED_GFF" ] || [ -z "$DOWNLOADED_FNA" ]; then
        skip "Alias test skipped" "Required files not available from download test"
        return
    fi
    
    if [ ! -f "$DOWNLOADED_GFF" ] || [ ! -f "$DOWNLOADED_FNA" ]; then
        skip "Alias test skipped" "Downloaded files not found"
        return
    fi
    
    print_test "Alias - Sequence ID matching"
    echo "Using GFF: $DOWNLOADED_GFF"
    echo "Using FNA: $DOWNLOADED_FNA"
    
    OUTPUT_GFF="$TEST_DIR/test_alias.gff3.gz"
    if annocli alias "$DOWNLOADED_GFF" "$DOWNLOADED_FNA" --output "$OUTPUT_GFF" 2>&1 | tee "$TEST_DIR/alias.log"; then
        # Check if output files were created
        if [ -f "$OUTPUT_GFF" ] && [ -s "$OUTPUT_GFF" ]; then
            # Check for mapping file
            MAPPING_FILE="${OUTPUT_GFF}.aliasMappings.tsv"
            if [ -f "$MAPPING_FILE" ]; then
                pass "Alias command successful (created aliasMatch file and mappings)"
            else
                fail "Alias mappings file not created" "Expected: $MAPPING_FILE"
            fi
        else
            fail "Alias output file not created or empty" "Expected: $OUTPUT_GFF"
        fi
    else
        fail "Alias command failed" "Check $TEST_DIR/alias.log for details"
    fi
}

# Test help and version
test_basics() {
    print_header "Testing basic functionality"
    
    # Test --help
    print_test "Help output"
    if annocli --help > /dev/null 2>&1; then
        pass "Help flag works"
    else
        fail "Help flag failed" "Command: annocli --help"
    fi
    
    # Test --version
    print_test "Version output"
    if annocli --version > /dev/null 2>&1; then
        pass "Version flag works"
    else
        fail "Version flag failed" "Command: annocli --version"
    fi
}

# Report results
report_results() {
    print_header "Test Results Summary"
    
    TOTAL=$((PASSED + FAILED + SKIPPED))
    echo -e "Total tests:   $TOTAL"
    echo -e "${GREEN}Passed:        $PASSED${NC}"
    echo -e "${RED}Failed:        $FAILED${NC}"
    echo -e "${YELLOW}Skipped:       $SKIPPED${NC}"
    
    if [ $FAILED -eq 0 ]; then
        echo -e "\n${GREEN}✓ All tests passed!${NC}"
        return 0
    else
        echo -e "\n${RED}✗ Some tests failed${NC}"
        return 1
    fi
}

# Main execution
main() {
    print_header "annocli Test Suite"
    echo "Testing all four commands with minimal API load"
    echo ""
    
    # Set up trap to cleanup on exit
    trap cleanup EXIT
    
    # Run setup
    setup
    
    # Run tests
    test_basics
    test_download
    test_summary
    test_stats
    test_alias
    
    # Report and exit
    if report_results; then
        exit 0
    else
        exit 1
    fi
}

# Run main
main
