import sys
import os

# Automatically tells pytest where src/ is before running any test
# This means all test files can do `from app import ...` cleanly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))