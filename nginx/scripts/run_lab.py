#!/usr/bin/env python3
"""Start local Python origins, launch one selected lab Nginx, and stop cleanly.

All sockets are bound strictly to 127.0.0.1.
Usage:
    python3 scripts/run_lab.py reverse-proxy/basic
    python3 scripts/run_lab.py --list
"""
import argparse
import http.server
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
LABS = {
    "reverse-proxy/basic": 8081,
    "reverse-proxy/advanced": 8082,
    "forward-proxy": 8083,
    "caching-server/basic": 8084,
    "caching-server/advanced": 8085,
    "load-balancer/basic": 8086,
    "load-balancer/advanced": 8087,
}



def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("lab", nargs="?", choices=sorted(LABS.keys()),
                        help="Lab to run (e.g. reverse-proxy/basic)")
    parser.add_argument("--list", action="store_true", help="List available labs and exit")
    parser.add_argument("--nginx", default=shutil.which("nginx"),
                        help="Path to nginx binary (default: searches PATH)")
    args = parser.parse_args()

    if args.list or not args.lab:
        print("Available Nginx practice labs:")
        for name, port in sorted(LABS.items()):
            print(f"  - {name:<26} (port {port})")
        return 0

    if not args.nginx:
        print("Error: 'nginx' was not found in PATH.", file=sys.stderr)
        print("Install Nginx or specify --nginx /path/to/nginx", file=sys.stderr)
        return 1

    binary = str(Path(args.nginx).resolve())
    lab_dir = ROOT / args.lab
    if not (lab_dir / "nginx.conf").is_file():
        print(f"Error: missing configuration at {lab_dir / 'nginx.conf'}", file=sys.stderr)
        return 1

    # Ensure required runtime subdirectories exist before launching
    for sub in ("logs", "temp/client", "temp/proxy", "temp/fastcgi",
                "temp/uwsgi", "temp/scgi", "cache/basic", "cache/advanced"):
        (lab_dir / sub).mkdir(parents=True, exist_ok=True)

    # Test configuration before starting services
    t_cmd = [binary, "-p", str(lab_dir) + "/", "-c", "nginx.conf", "-t"]
    test_run = subprocess.run(t_cmd, capture_output=True, text=True)
    if test_run.returncode != 0:
        print("Nginx configuration test failed:", file=sys.stderr)
        print(test_run.stderr, file=sys.stderr)
        return 1

    # Bind synchronously: a port conflict must stop startup, not leave a
    # background thread dead while Nginx proxies an unrelated application.
    from functools import partial
    import socket
    servers = []
    try:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", LABS[args.lab]))
        for port, site in ((9001, "site-a"), (9002, "site-b")):
            handler = partial(http.server.SimpleHTTPRequestHandler,
                              directory=str(ROOT / "fixtures" / site))
            servers.append(http.server.ThreadingHTTPServer(("127.0.0.1", port), handler))
    except OSError as error:
        for server in servers:
            server.server_close()
        print(f"Cannot bind a lab port: {error}", file=sys.stderr)
        return 1
    threads = [threading.Thread(target=server.serve_forever, daemon=True)
               for server in servers]
    for thread in threads:
        thread.start()

    # Launch Nginx in the foreground
    global_flags = "daemon off;" + (" user root;" if os.geteuid() == 0 else "")
    cmd = [binary, "-p", str(lab_dir) + "/", "-c", "nginx.conf", "-g", global_flags]
    print(f"[*] Starting {args.lab} on http://127.0.0.1:{LABS[args.lab]}/")
    print("    Origins: 127.0.0.1:9001 (Site A), 127.0.0.1:9002 (Site B)")
    print("    Press Ctrl+C to stop.\n")

    try:
        proc = subprocess.Popen(cmd)
    except OSError as error:
        for server in servers:
            server.shutdown()
            server.server_close()
        print(f"Cannot launch Nginx: {error}", file=sys.stderr)
        return 1

    def shutdown(signum, frame):
        if proc.poll() is None:
            proc.terminate()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        proc.wait()
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        for server in servers:
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(timeout=1)
    return 0 if proc.returncode in (0, -signal.SIGTERM) else proc.returncode


if __name__ == "__main__":
    sys.exit(main() or 0)
