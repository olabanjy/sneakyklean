#!/bin/bash

# Sneaky Klean Test Runner Script
# Runs Django tests in Docker container

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   Sneaky Klean - Test Runner${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Parse arguments
COVERAGE=false
APP=""
VERBOSE=""

for arg in "$@"; do
    case $arg in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE="--verbosity=2"
            shift
            ;;
        accounts|orders|core)
            APP=$arg
            shift
            ;;
        *)
            # Unknown option
            ;;
    esac
done

# Function to run tests
run_tests() {
    if [ "$COVERAGE" = true ]; then
        echo -e "${YELLOW}📊 Running tests with coverage...${NC}"
        echo ""
        
        # Install coverage if not installed
        docker-compose run --rm web pip install coverage -q
        
        # Run tests with coverage
        docker-compose run --rm web coverage run --source='.' manage.py test $APP $VERBOSE
        
        echo ""
        echo -e "${BLUE}📈 Coverage Report:${NC}"
        docker-compose run --rm web coverage report
        
        echo ""
        echo -e "${GREEN}✅ Coverage HTML report generated${NC}"
        echo "To view: docker-compose run --rm web coverage html"
        echo "Then open htmlcov/index.html in your browser"
    else
        echo -e "${YELLOW}🧪 Running tests...${NC}"
        echo ""
        
        if [ -z "$APP" ]; then
            docker-compose run --rm web python manage.py test $VERBOSE
        else
            echo -e "${BLUE}Testing $APP app only${NC}"
            docker-compose run --rm web python manage.py test $APP $VERBOSE
        fi
    fi
}

# Check if containers are built
if ! docker-compose ps web | grep -q 'sneakyklean'; then
    echo -e "${YELLOW}⚙️  Building containers first...${NC}"
    docker-compose build web
fi

# Run tests
run_tests
TEST_EXIT_CODE=$?

echo ""
echo -e "${BLUE}================================================${NC}"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo "Review the output above for details"
fi

echo -e "${BLUE}================================================${NC}"
echo ""

# Summary
if [ -z "$APP" ]; then
    echo "📊 Test Summary:"
    echo "   - Accounts: 26 tests"
    echo "   - Orders:   22 tests"
    echo "   - Core:     19 tests"
    echo "   - Total:    67 tests"
else
    echo "📊 Tested: $APP app"
fi

echo ""
echo "💡 Usage tips:"
echo "   ./run_tests.sh              - Run all tests"
echo "   ./run_tests.sh accounts     - Run accounts tests only"
echo "   ./run_tests.sh --coverage   - Run with coverage report"
echo "   ./run_tests.sh --verbose    - Run with detailed output"
echo ""

exit $TEST_EXIT_CODE
