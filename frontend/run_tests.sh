#!/bin/bash

# Change to the script directory
cd "$(dirname "$0")"

# Run the tests
npm run test

# Return to the original directory
cd - > /dev/null
