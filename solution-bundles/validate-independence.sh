#!/bin/bash
# Solution Bundle Independence Validation Script
# Verifies that each solution is truly self-contained and independent

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Solutions to validate
SOLUTIONS=(
    "01-single-site-disk"
    "02-multisite-disk"
    "03-blueprint-configuration"
    "04-configuration-drift"
    "05-tape-archival"
    "06-cloud-storage"
    "07-petascale-protection"
    "08-multi-tenant"
)

echo "=========================================="
echo "Solution Bundle Independence Validation"
echo "=========================================="
echo ""

# Function to check if a solution exists
check_solution_exists() {
    local solution=$1
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -d "$solution" ]; then
        echo -e "${GREEN}✓${NC} Solution directory exists: $solution"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} Solution directory missing: $solution"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to check if README exists
check_readme() {
    local solution=$1
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -f "$solution/README.md" ]; then
        echo -e "${GREEN}✓${NC} README.md exists: $solution"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} README.md missing: $solution"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to check if playbooks directory exists
check_playbooks() {
    local solution=$1
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -d "$solution/playbooks" ]; then
        local count=$(find "$solution/playbooks" -name "*.yml" -o -name "*.yaml" | wc -l)
        if [ "$count" -gt 0 ]; then
            echo -e "${GREEN}✓${NC} Playbooks exist ($count files): $solution"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        else
            echo -e "${YELLOW}⚠${NC} Playbooks directory empty: $solution"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        fi
    else
        echo -e "${RED}✗${NC} Playbooks directory missing: $solution"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to check if roles are vendored
check_roles() {
    local solution=$1
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -d "$solution/roles" ]; then
        local count=$(find "$solution/roles" -maxdepth 1 -type d | wc -l)
        if [ "$count" -gt 1 ]; then
            echo -e "${GREEN}✓${NC} Roles vendored ($((count-1)) roles): $solution"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        else
            echo -e "${YELLOW}⚠${NC} Roles directory empty: $solution"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        fi
    else
        echo -e "${RED}✗${NC} Roles directory missing: $solution"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to check if plugins are vendored
check_plugins() {
    local solution=$1
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -d "$solution/plugins" ]; then
        local count=$(find "$solution/plugins" -name "*.py" | wc -l)
        if [ "$count" -gt 0 ]; then
            echo -e "${GREEN}✓${NC} Plugins vendored ($count files): $solution"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        else
            echo -e "${YELLOW}⚠${NC} Plugins directory empty: $solution"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        fi
    else
        echo -e "${RED}✗${NC} Plugins directory missing: $solution"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to check for external dependencies
check_no_external_deps() {
    local solution=$1
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -f "$solution/requirements.yml" ]; then
        # Check if requirements.yml only contains ansible.builtin or is empty
        local external_deps=$(grep -v "^#" "$solution/requirements.yml" | grep -v "ansible.builtin" | grep -v "^---" | grep -v "^$" | grep "name:" | wc -l)
        
        if [ "$external_deps" -eq 0 ]; then
            echo -e "${GREEN}✓${NC} No external dependencies: $solution"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        else
            echo -e "${RED}✗${NC} External dependencies found: $solution"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        fi
    else
        echo -e "${YELLOW}⚠${NC} requirements.yml missing: $solution"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    fi
}

# Function to check for cross-solution references
check_no_cross_references() {
    local solution=$1
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    # Search for references to other solution directories
    local cross_refs=0
    for other_solution in "${SOLUTIONS[@]}"; do
        if [ "$solution" != "$other_solution" ]; then
            if grep -r "../$other_solution" "$solution" 2>/dev/null | grep -v ".git" > /dev/null; then
                cross_refs=$((cross_refs + 1))
            fi
        fi
    done
    
    if [ "$cross_refs" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} No cross-solution references: $solution"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} Cross-solution references found: $solution"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Main validation loop
for solution in "${SOLUTIONS[@]}"; do
    echo ""
    echo "Validating: $solution"
    echo "----------------------------------------"
    
    check_solution_exists "$solution"
    check_readme "$solution"
    check_playbooks "$solution"
    check_roles "$solution"
    check_plugins "$solution"
    check_no_external_deps "$solution"
    check_no_cross_references "$solution"
done

# Summary
echo ""
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo -e "Total Checks:  $TOTAL_CHECKS"
echo -e "${GREEN}Passed:        $PASSED_CHECKS${NC}"
echo -e "${RED}Failed:        $FAILED_CHECKS${NC}"
echo ""

if [ "$FAILED_CHECKS" -eq 0 ]; then
    echo -e "${GREEN}✓ All solutions are independent and self-contained!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some solutions have dependency issues.${NC}"
    exit 1
fi

# Made with Bob
