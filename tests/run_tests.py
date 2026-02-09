import unittest
import sys
import os

def setup_logging():
    print("="*40)
    print("   AI-Discord Bot Test Runner   ")
    print("="*40)
    print(f"Python: {sys.version}")
    print(f"Root: {os.getcwd()}")
    print("-" * 40)

def run_tests():
    setup_logging()
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ All Tests PASSED!")
        sys.exit(0)
    else:
        print(f"\n❌ Some Tests FAILED (Failures={len(result.failures)}, Errors={len(result.errors)})")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
