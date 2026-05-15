import subprocess
import sys
from datetime import datetime

day_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
command = [
    "pytest",
    "--md-report",
    "--md-report-verbose=1",
    f"--md-report-output=tests/test_reports/report_{day_time}.md",
    "tests/"
]

try:
    result = subprocess.run(command, check=True)
    print(f"Tests completed successfully with exit code {result.returncode}")
except subprocess.CalledProcessError as e:
    print(f"Pytest failed with exit code {e.returncode}")
    sys.exit(e.returncode)