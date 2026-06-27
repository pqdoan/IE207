import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))


IS_WINDOWS = os.name == "nt"


def find_pids_using_port(port: int):
    if IS_WINDOWS:
        try:
            output = subprocess.check_output(["netstat", "-ano", "-p", "tcp"], text=True, stderr=subprocess.STDOUT)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            output = getattr(exc, "output", "") or ""

        pids = []
        for line in output.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                match = re.search(r"\s+(\d+)\s*$", line)
                if match:
                    pids.append(int(match.group(1)))
        return sorted(set(pids))

    # Linux / macOS: dùng lsof nếu có
    pids = []
    try:
        output = subprocess.check_output(["lsof", "-t", f"-i:{port}"], text=True, stderr=subprocess.DEVNULL)
        pids = [int(p) for p in output.split()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return sorted(set(pids))


def kill_pids(pids):
    for pid in pids:
        try:
            if IS_WINDOWS:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            else:
                os.kill(pid, signal.SIGKILL)
            print(f"Stopped process {pid}")
        except Exception as exc:
            print(f"Unable to stop process {pid}: {exc}")
    time.sleep(1)


def is_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def main():
    print(f"Checking port {HOST}:{PORT}...")
    pids = find_pids_using_port(PORT)
    if pids:
        print(f"Found process(es) using port {PORT}: {pids}")
        kill_pids(pids)

    if not is_port_free(HOST, PORT):
        print(f"Port {PORT} is still busy. Please close the process manually and try again.")
        sys.exit(1)

    cmd = [sys.executable, "-m", "uvicorn", "backend:app", "--host", HOST, "--port", str(PORT)]
    print("Starting backend with:", " ".join(cmd))
    subprocess.call(cmd, cwd=str(Path(__file__).resolve().parent))


if __name__ == "__main__":
    main()
