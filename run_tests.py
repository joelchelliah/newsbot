#!/usr/bin/env python3
"""
Simple test runner for the newsbot application
"""

import sys
import os

# Add the current directory to Python path so tests can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🧪 Running NewsBot Tests...")
    print("=" * 50)

    # Run the embedding tests
    from tests.test_embeddings import test_embeddings

    try:
        test_embeddings()
        print("\n✅  All tests completed successfully!")
    except Exception as e:
        print(f"\n❌  Test failed with error: {e}")
        sys.exit(1)
