import os
from pyats.easypy import run

def main(runtime):
    testbed = runtime.testbed
    here = os.path.dirname(__file__)
    testscript = os.path.join(here, "tests", "test_ping_routes.py")
    run(testscript=testscript, testbed=testbed)

