#!/bin/bash

# Change to the script directory
cd "$(dirname "$0")"

echo "===== Running Backend Tests ====="
cd backend
./run_tests.sh
BACKEND_RESULT=$?
cd ..

echo ""
echo "===== Running Frontend Tests ====="
cd frontend
./run_tests.sh
FRONTEND_RESULT=$?
cd ..

# Return overall status
if [ $BACKEND_RESULT -eq 0 ] && [ $FRONTEND_RESULT -eq 0 ]; then
  echo ""
  echo "✅ All tests passed!"
  exit 0
else
  echo ""
  echo "❌ Some tests failed!"
  exit 1
fi
