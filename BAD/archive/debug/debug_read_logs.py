import sys
import os

log_files = ["logs/bot_dev.log", "logs/console_output.log"]

for log_file in log_files:
    if os.path.exists(log_file):
        print(f"--- Content of {log_file} ---")
        try:
            with open(log_file, "r", encoding="utf-16") as f:
                print(f.read())
        except Exception as e:
            print(f"Error reading {log_file} as utf-16: {e}")
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    print(f.read())
            except Exception as e2:
                print(f"Error reading {log_file} as utf-8: {e2}")
