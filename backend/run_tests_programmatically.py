import pytest

def run_tests():
    result = pytest.main(["-q"])
    return result == 0