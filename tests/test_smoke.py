import os
import subprocess
import sys

def test_run_all_smoke():
    env = os.environ.copy()
    env["COUNTRIES"] = "HR"
    subprocess.check_call([sys.executable, "-m", "src.run_all"], env=env)