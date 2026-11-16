import subprocess
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

dashboard = None
collector = None

def stop_process(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

try:
    print("\nSTARTING DERIV DIGIT INTELLIGENCE BOT")
    print("====================================")

    dashboard = subprocess.Popen(
        [sys.executable, "-u", "dashboard.py"],
        cwd=PROJECT_DIR
    )

    time.sleep(2)

    if dashboard.poll() is not None:
        raise RuntimeError(
            "Dashboard failed to start. Check whether port 8000 is already in use."
        )

    print("\nDashboard running at http://127.0.0.1:8000")

    while True:
        print("\nStarting 5,000-tick collection cycle...")

        collector = subprocess.Popen(
            [sys.executable, "-u", "deriv_analyzer.py"],
            cwd=PROJECT_DIR
        )

        exit_code = collector.wait()
        collector = None

        if dashboard.poll() is not None:
            raise RuntimeError("Dashboard stopped unexpectedly.")

        print(f"\nCollection cycle ended (exit code {exit_code}).")
        print("Restarting collector in 5 seconds...")
        time.sleep(5)

except KeyboardInterrupt:
    print("\nStopping bot...")

except Exception as error:
    print(f"\nERROR: {error}")

finally:
    stop_process(collector)
    stop_process(dashboard)
    print("Bot stopped.")
