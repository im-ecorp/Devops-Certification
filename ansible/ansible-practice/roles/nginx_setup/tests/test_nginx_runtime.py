"""Optional real Nginx tests: set NGINX_TEST_BINARY to an isolated binary."""
import os
from pathlib import Path
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen

import pytest
from test_templates import DEFAULTS, ENV

BINARY = os.environ.get("NGINX_TEST_BINARY")
pytestmark = pytest.mark.skipif(not BINARY, reason="NGINX_TEST_BINARY is not set")


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def configure(directory, sites):
    context = dict(DEFAULTS, ansible_managed="test",
                   nginx_proxy_params_path=str(directory / "proxy.conf"))
    for template, name in [("proxy_params.j2", "proxy.conf"),
                           ("websocket_map.conf.j2", "map.conf")]:
        (directory / name).write_text(ENV.get_template(template).render(**context))
    for index, site in enumerate(sites):
        (directory / f"site-{index}.conf").write_text(
            ENV.get_template("site.conf.j2").render(**context, item=site))
    config = directory / "nginx.conf"
    config.write_text(f"""pid {directory}/nginx.pid;
error_log stderr;
events {{ worker_connections 64; }}
http {{
    access_log off;
    client_body_temp_path {directory}/body;
    proxy_temp_path {directory}/proxy;
    fastcgi_temp_path {directory}/fastcgi;
    uwsgi_temp_path {directory}/uwsgi;
    scgi_temp_path {directory}/scgi;
    include {directory}/map.conf;
    include {directory}/site-*.conf;
}}
""")
    return config


def test_nginx_accepts_http_static_and_tls_config(tmp_path):
    cert, key = tmp_path / "cert.pem", tmp_path / "key.pem"
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                    "-keyout", str(key), "-out", str(cert), "-days", "1",
                    "-subj", "/CN=tls.example.com"], check=True, capture_output=True)
    sites = [dict(server_name="app.example.com", proxy_pass="http://127.0.0.1:9000",
                  listen_port=free_port()),
             dict(server_name="static.example.com", root=str(tmp_path), listen_port=free_port()),
             dict(server_name="tls.example.com", proxy_pass="https://127.0.0.1:9001",
                  listen_port=free_port(), ssl_port=free_port(), ssl_enabled=True,
                  ssl_cert_path=str(cert), ssl_key_path=str(key))]
    config = configure(tmp_path, sites)
    result = subprocess.run([BINARY, "-e", "stderr", "-t", "-p", str(tmp_path),
                             "-c", str(config)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "test is successful" in result.stderr


def test_live_proxy_preserves_path_and_upgrade_headers(tmp_path):
    class Backend(BaseHTTPRequestHandler):
        def do_GET(self):
            body = (self.path + "|" + self.headers.get("Upgrade", "") + "|" +
                    self.headers.get("Connection", "") + "|" +
                    self.headers.get("X-Forwarded-Proto", "")).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    backend = ThreadingHTTPServer(("127.0.0.1", 0), Backend)
    thread = threading.Thread(target=backend.serve_forever, daemon=True)
    thread.start()
    port = free_port()
    config = configure(tmp_path, [dict(server_name="app.example.com", listen_port=port,
                                      proxy_pass=f"http://127.0.0.1:{backend.server_port}")])
    process = subprocess.Popen([BINARY, "-e", "stderr", "-p", str(tmp_path),
                                "-c", str(config), "-g", "daemon off;"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for _ in range(50):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                    break
            except OSError:
                time.sleep(0.1)
        request = Request(f"http://127.0.0.1:{port}/path?query=1",
                          headers={"Host": "app.example.com", "Upgrade": "websocket"})
        with urlopen(request, timeout=5) as response:
            assert response.read().decode() == "/path?query=1|websocket|upgrade|http"
    finally:
        process.terminate()
        process.communicate(timeout=5)
        backend.shutdown()
        backend.server_close()
