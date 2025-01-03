#!/bin/bash
#
# Run project through linting
#
# NOTE: This script expects to be run from the project root with
# ./scripts/run_lint_python.sh

function display_result {
  RESULT=$1
  EXIT_STATUS=$2
  TEST=$3

  if [ $RESULT -ne 0 ]; then
    echo -e "\033[31m$TEST failed\033[0m"
    exit $EXIT_STATUS
  else
    echo -e "\033[32m$TEST passed\033[0m"
  fi
}

ruff check .
display_result $? 1 "Ruff code style check (including isort)"

# pylint bit encodes the exit code to allow you to figure out which category has failed.
# https://docs.pylint.org/en/1.6.0/run.html#exit-codes
# We want to fail on all errors so don't check for specific bits in the output; but if we did in future, see:
# http://stackoverflow.com/questions/6626351/how-to-extract-bits-from-return-code-number-in-bash
find . -type f -name "*.py" | xargs pylint --reports=n --output-format=colorized --rcfile=.pylintrc -j 0
display_result $? 1 "Pylint linting check"

./scripts/run_mypy.sh
display_result $? 1 "Mypy type check"

black --check . --exclude node_modules
display_result $? 1 "Python code formatting check"
