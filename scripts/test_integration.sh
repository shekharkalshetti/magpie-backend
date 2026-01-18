#!/bin/bash

# End-to-End Integration Test for ReviewQueue System
# This script verifies that all components work together correctly

echo "=================================================="
echo "Triton ReviewQueue System - Integration Test"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
test_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

test_fail() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

test_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "Test Suite 1: Module Imports"
echo "=============================="

# Test 1: ReviewQueue Model Import
if python -c "from src.review_queue.models import ReviewQueue, ContentType, ReviewStatus, ModerationSeverity" 2>/dev/null; then
    test_pass "ReviewQueue model imports successfully"
else
    test_fail "ReviewQueue model import failed"
fi

# Test 2: ReviewQueue Service Import
if python -c "from src.review_queue.service import ReviewQueueService" 2>/dev/null; then
    test_pass "ReviewQueue service imports successfully"
else
    test_fail "ReviewQueue service import failed"
fi

# Test 3: ReviewQueue Router Import
if python -c "from src.review_queue.router import router" 2>/dev/null; then
    test_pass "ReviewQueue router imports successfully"
else
    test_fail "ReviewQueue router import failed"
fi

# Test 4: Celery App Import
if python -c "from src.tasks.celery_app import app" 2>/dev/null; then
    test_pass "Celery app imports successfully"
else
    test_fail "Celery app import failed"
fi

# Test 5: Moderation Task Import
if python -c "from src.tasks.moderation_tasks import moderate_output" 2>/dev/null; then
    test_pass "Moderation task imports successfully"
else
    test_fail "Moderation task import failed"
fi

echo ""
echo "Test Suite 2: Celery Configuration"
echo "==================================="

# Test 6: Celery Broker Configuration
BROKER=$(python -c "from src.tasks.celery_app import app; print(app.conf.broker_url)" 2>/dev/null)
if [ -n "$BROKER" ]; then
    test_pass "Celery broker configured: $BROKER"
else
    test_fail "Celery broker configuration missing"
fi

# Test 7: Celery Result Backend Configuration
BACKEND=$(python -c "from src.tasks.celery_app import app; print(app.conf.result_backend)" 2>/dev/null)
if [ -n "$BACKEND" ]; then
    test_pass "Celery result backend configured: $BACKEND"
else
    test_fail "Celery result backend configuration missing"
fi

# Test 8: Task Registration
if python << 'EOF' 2>/dev/null
from src.tasks.celery_app import app
from src.tasks.moderation_tasks import moderate_output
assert 'src.tasks.moderation_tasks.moderate_output' in app.tasks
EOF
then
    test_pass "Moderation task is registered with Celery"
else
    test_fail "Moderation task registration failed"
fi

echo ""
echo "Test Suite 3: FastAPI Integration"
echo "=================================="

# Test 9: Main App Loads
if python -c "from src.main import app; assert app is not None" 2>/dev/null; then
    test_pass "FastAPI app loads successfully"
else
    test_fail "FastAPI app failed to load"
fi

# Test 10: ReviewQueue Routes Registered
ROUTE_COUNT=$(python -c "from src.main import app; routes = [r.path for r in app.routes if 'review' in r.path.lower()]; print(len(routes))" 2>/dev/null)
if [ "$ROUTE_COUNT" == "4" ]; then
    test_pass "All 4 ReviewQueue routes registered"
else
    test_fail "ReviewQueue routes not properly registered (found $ROUTE_COUNT, expected 4)"
fi

# Test 11: List Review Queue Route
if python -c "from src.main import app; routes = [r.path for r in app.routes]; assert '/api/v1/projects/{project_id}/review-queue' in routes" 2>/dev/null; then
    test_pass "GET /api/v1/projects/{project_id}/review-queue registered"
else
    test_fail "GET /projects/{project_id}/review-queue route missing"
fi

# Test 12: Get Stats Route
if python -c "from src.main import app; routes = [r.path for r in app.routes]; assert '/api/v1/projects/{project_id}/review-queue/stats' in routes" 2>/dev/null; then
    test_pass "GET /api/v1/projects/{project_id}/review-queue/stats registered"
else
    test_fail "GET /projects/{project_id}/review-queue/stats route missing"
fi

# Test 13: Get Item Route
if python -c "from src.main import app; routes = [r.path for r in app.routes]; assert '/api/v1/review-queue/{item_id}' in routes" 2>/dev/null; then
    test_pass "GET /api/v1/review-queue/{item_id} registered"
else
    test_fail "GET /review-queue/{item_id} route missing"
fi

# Test 14: Update Item Route
if python -c "from src.main import app; methods = {}; [methods.update({r.path: r.methods}) for r in app.routes]; assert 'PATCH' in methods.get('/api/v1/review-queue/{item_id}', set())" 2>/dev/null; then
    test_pass "PATCH /api/v1/review-queue/{item_id} registered"
else
    test_fail "PATCH /review-queue/{item_id} route missing or no PATCH method"
fi

echo ""
echo "Test Suite 4: Pydantic Schemas"
echo "=============================="

# Test 15: ReviewQueueResponse Schema
if python -c "from src.review_queue.schemas import ReviewQueueItemResponse; print(ReviewQueueItemResponse.model_fields.keys())" 2>/dev/null | grep -q "id"; then
    test_pass "ReviewQueueItemResponse schema is valid"
else
    test_fail "ReviewQueueItemResponse schema validation failed"
fi

# Test 16: ReviewQueueStatsResponse Schema
if python -c "from src.review_queue.schemas import ReviewQueueStatsResponse; print(ReviewQueueStatsResponse.model_fields.keys())" 2>/dev/null | grep -q "total"; then
    test_pass "ReviewQueueStatsResponse schema is valid"
else
    test_fail "ReviewQueueStatsResponse schema validation failed"
fi

echo ""
echo "Test Suite 5: External Services"
echo "==============================="

# Test 17: Redis Connection (Optional)
if redis-cli ping > /dev/null 2>&1; then
    test_pass "Redis is running and accessible"
else
    test_warning "Redis is not running (required for Celery tasks)"
fi

echo ""
echo "=================================================="
echo "Integration Test Results"
echo "=================================================="
echo -e "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Tests Failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "System is ready for deployment. Next steps:"
    echo "1. Start Redis (if not running):"
    echo "   redis-server"
    echo ""
    echo "2. Run database migration:"
    echo "   python -m alembic upgrade head"
    echo ""
    echo "3. Start FastAPI server:"
    echo "   python -m uvicorn src.main:app --reload --port 8000"
    echo ""
    echo "4. Start Celery worker (in another terminal):"
    echo "   bash scripts/start_celery_worker.sh"
    echo ""
    echo "5. Access API documentation:"
    echo "   http://localhost:8000/docs"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review the errors above.${NC}"
    exit 1
fi
