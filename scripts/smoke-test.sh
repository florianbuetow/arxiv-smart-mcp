#!/usr/bin/env bash
# Smoke test for arxivsmart service.
# Starts the service, runs curl checks against all endpoints, and exits 1 on any failure.
# Usage: bash scripts/smoke-test.sh

set -euo pipefail

BASE_URL="http://127.0.0.1:7001"
PASS=0
FAIL=0
SKIP=0
PID=""

cleanup() {
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo ""
        echo "--- Shutting down service (pid $PID) ---"
        curl -sS -X POST "$BASE_URL/v1/shutdown" -H "Content-Type: application/json" > /dev/null 2>&1 || true
        sleep 1
        kill "$PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

assert_status() {
    local label="$1"
    local expected="$2"
    local actual="$3"

    if [ "$actual" = "$expected" ]; then
        echo "  PASS  $label (HTTP $actual)"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $label (expected HTTP $expected, got HTTP $actual)"
        FAIL=$((FAIL + 1))
    fi
}

assert_json_field() {
    local label="$1"
    local json="$2"
    local field="$3"
    local expected="$4"

    actual=$(echo "$json" | python3 -c "import sys,json; print(json.load(sys.stdin)$field)" 2>/dev/null || echo "__ERROR__")
    if [ "$actual" = "$expected" ]; then
        echo "  PASS  $label ($field == $expected)"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $label ($field: expected '$expected', got '$actual')"
        FAIL=$((FAIL + 1))
    fi
}

skip_test() {
    local label="$1"
    local reason="$2"
    echo "  SKIP  $label ($reason)"
    SKIP=$((SKIP + 1))
}

# --- Start service ---
echo "=== Starting arxivsmart service ==="
uv run src/main.py &
PID=$!
echo "Service pid: $PID"

# Wait for service to be ready
echo "Waiting for service..."
for i in $(seq 1 15); do
    if curl -s "$BASE_URL/v1/health" > /dev/null 2>&1; then
        echo "Service ready after ${i}s"
        break
    fi
    if [ "$i" = "15" ]; then
        echo "FAIL: Service did not start within 15 seconds"
        exit 1
    fi
    sleep 1
done

echo ""
echo "=== Running smoke tests ==="

# --- 1. Health endpoint ---
echo ""
echo "--- GET /v1/health ---"
RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/v1/health")
HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
assert_status "health status code" "200" "$HTTP_CODE"
assert_json_field "health body" "$BODY" "['data']['status']" "healthy"

# --- 2. Info endpoint ---
echo ""
echo "--- GET /v1/info ---"
RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/v1/info")
HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
assert_status "info status code" "200" "$HTTP_CODE"
assert_json_field "info has config" "$BODY" "['status']" "200"

# --- 3. Search endpoint ---
echo ""
echo "--- POST /v1/search ---"
sleep 3  # respect rate limit
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/v1/search" \
    -H "Content-Type: application/json" \
    -d '{"query":"attention is all you need","start":0,"max_results":2,"sort_by":"relevance","sort_order":"descending"}')
HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
assert_status "search status code" "200" "$HTTP_CODE"
assert_json_field "search envelope status" "$BODY" "['status']" "200"

PAPER_COUNT=$(echo "$BODY" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['data']['papers']))" 2>/dev/null || echo "0")
if [ "$PAPER_COUNT" -gt "0" ]; then
    echo "  PASS  search returned $PAPER_COUNT papers"
    PASS=$((PASS + 1))
else
    echo "  FAIL  search returned 0 papers"
    FAIL=$((FAIL + 1))
fi

# Extract an arxiv_id for subsequent tests
ARXIV_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['papers'][0]['arxiv_id'])" 2>/dev/null || echo "")
echo "  Using paper: $ARXIV_ID"

# --- 4. Search validation (empty query) ---
echo ""
echo "--- POST /v1/search (invalid) ---"
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/v1/search" \
    -H "Content-Type: application/json" \
    -d '{"query":"","start":0,"max_results":10,"sort_by":"relevance","sort_order":"descending"}')
HTTP_CODE=$(echo "$RESP" | tail -1)
assert_status "search validation rejects empty query" "400" "$HTTP_CODE"

# --- 5. Paper detail endpoint ---
echo ""
echo "--- GET /v1/paper/{id} ---"
if [ -n "$ARXIV_ID" ]; then
    sleep 3
    RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/v1/paper/$ARXIV_ID")
    HTTP_CODE=$(echo "$RESP" | tail -1)
    BODY=$(echo "$RESP" | sed '$d')
    assert_status "paper detail status code" "200" "$HTTP_CODE"
    assert_json_field "paper detail has arxiv_id" "$BODY" "['data']['arxiv_id']" "$ARXIV_ID"
else
    skip_test "paper detail" "no arxiv_id from search"
fi

# --- 6. PDF download ---
echo ""
echo "--- GET /v1/paper/{id}/pdf ---"
if [ -n "$ARXIV_ID" ]; then
    sleep 3
    RESP=$(curl -s -o /dev/null -w "%{http_code} %{content_type} %{size_download}" "$BASE_URL/v1/paper/$ARXIV_ID/pdf")
    HTTP_CODE=$(echo "$RESP" | awk '{print $1}')
    CONTENT_TYPE=$(echo "$RESP" | awk '{print $2}')
    SIZE=$(echo "$RESP" | awk '{print $3}')
    assert_status "pdf download status code" "200" "$HTTP_CODE"
    if echo "$CONTENT_TYPE" | grep -q "application/pdf"; then
        echo "  PASS  pdf content-type is application/pdf"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  pdf content-type: expected application/pdf, got $CONTENT_TYPE"
        FAIL=$((FAIL + 1))
    fi
    if [ "${SIZE%.*}" -gt "1000" ]; then
        echo "  PASS  pdf size is ${SIZE%.*} bytes (> 1KB)"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  pdf size too small: ${SIZE%.*} bytes"
        FAIL=$((FAIL + 1))
    fi
else
    skip_test "pdf download" "no arxiv_id from search"
fi

# --- 7. HTML endpoint ---
echo ""
echo "--- GET /v1/paper/{id}/html ---"
if [ -n "$ARXIV_ID" ]; then
    sleep 3
    RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/v1/paper/$ARXIV_ID/html")
    HTTP_CODE=$(echo "$RESP" | tail -1)
    if [ "$HTTP_CODE" = "200" ]; then
        assert_status "html endpoint status code" "200" "$HTTP_CODE"
    elif [ "$HTTP_CODE" = "502" ]; then
        skip_test "html endpoint" "ar5iv.labs.arxiv.org unreachable (502)"
    else
        assert_status "html endpoint status code" "200" "$HTTP_CODE"
    fi
else
    skip_test "html endpoint" "no arxiv_id from search"
fi

# --- 8. Markdown endpoint ---
echo ""
echo "--- GET /v1/paper/{id}/markdown ---"
if [ -n "$ARXIV_ID" ]; then
    sleep 3
    RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/v1/paper/$ARXIV_ID/markdown")
    HTTP_CODE=$(echo "$RESP" | tail -1)
    if [ "$HTTP_CODE" = "200" ]; then
        assert_status "markdown endpoint status code" "200" "$HTTP_CODE"
    elif [ "$HTTP_CODE" = "502" ]; then
        skip_test "markdown endpoint" "ar5iv.labs.arxiv.org unreachable (502)"
    else
        assert_status "markdown endpoint status code" "200" "$HTTP_CODE"
    fi
else
    skip_test "markdown endpoint" "no arxiv_id from search"
fi

# --- Summary ---
echo ""
echo "=== Results ==="
echo "  Passed:  $PASS"
echo "  Failed:  $FAIL"
echo "  Skipped: $SKIP"

if [ "$FAIL" -gt "0" ]; then
    echo ""
    echo "FAILED ($FAIL failures)"
    exit 1
else
    echo ""
    echo "ALL PASSED"
    exit 0
fi
