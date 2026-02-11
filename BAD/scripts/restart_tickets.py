
import os
import sys
import subprocess
import time
import socket
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format='🔄 %(message)s')

def get_pid_using_netstat(port):
    """
    Finds the PID of the process using the specified port on Windows using netstat.
    """
    try:
        # Run netstat -ano
        cmd = "netstat -ano"
        # Use simple Popen or check_output
        output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
        
        target = f":{port}"
        for line in output.splitlines():
            if target in line and "LISTENING" in line:
                # Line format: Protocol LocalAddress ForeignAddress State PID
                # TCP    127.0.0.1:45678        0.0.0.0:0              LISTENING       1234
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    logging.info(f"Found process listening on port {port}: PID {pid}")
                    return int(pid)
    except subprocess.CalledProcessError as e:
        logging.error(f"Netstat command failed: {e}")
    except Exception as e:
        logging.error(f"Error parsing netstat output: {e}")
    return None

def kill_process(pid):
    """Kills a process by PID."""
    try:
        subprocess.check_call(f"taskkill /F /PID {pid}", shell=True)
        logging.info(f"✅ Killed PID {pid}")
        return True
    except subprocess.CalledProcessError:
        logging.warning(f"⚠️ Failed to kill PID {pid} (might be already gone)")
        return False

def main():
    SCRIPT_NAME = "tickets_assistant.py"
    SCRIPT_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'bridge', SCRIPT_NAME)
    
    # 1. Check for old instance
    logging.info(f"Checking for existing Ticket Assistant (Port 45678)...")
    pid = get_pid_using_netstat(45678)
    
    if pid:
        # Check if it's OUR PID (don't kill self if we were running the script directly, but here we are running run_dev.py)
        # But wait, we are running restart_tickets.py. The target is tickets_assistant.py. Safe.
        logging.info(f"found running instance (PID: {pid}). Termination imminent...")
        kill_process(pid)
        time.sleep(1) # Grace period
    else:
        logging.info("Clean slate. No old instance found.")

    # 2. Start new instance
    logging.info(f"🚀 Starting Ticket Assistant...")
    try:
        # Stream the output directly to the console
        subprocess.run([sys.executable, "-u", SCRIPT_PATH], check=True)
    except KeyboardInterrupt:
        logging.info("\n🛑 Stopped by user.")
    except Exception as e:
        logging.error(f"❌ Failed to start bot: {e}")

if __name__ == "__main__":
    main()
