"""Render routing templates independently of a live inventory or service."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
import yaml

ROLE = Path(__file__).resolve().parents[1]
DEFAULTS = yaml.safe_load((ROLE / "defaults/main.yml").read_text())
ENV = Environment(loader=FileSystemLoader(ROLE / "templates"), undefined=StrictUndefined,
                  trim_blocks=True, lstrip_blocks=True)


def render_site(**site):
    return ENV.get_template("site.conf.j2").render(
        **DEFAULTS, item=site, ansible_managed="Ansible managed")


def test_http_proxy_preserves_uri_and_supports_websockets():
    text = render_site(name="app", server_name="app.example.com",
                       proxy_pass="http://127.0.0.1:8080")
    assert "proxy_pass http://127.0.0.1:8080;" in text
    assert "proxy_http_version 1.1;" in text
    assert "include /etc/nginx/snippets/nginx-setup-proxy-params.conf;" in text
    assert "ssl_certificate" not in text

def test_https_proxy_with_backend_tls_sni():
    text = render_site(name="secure_app", server_name="secure.example.com",
                       proxy_pass="https://10.0.0.5:8443",
                       ssl_enabled=True, ssl_cert_path="/etc/ssl/cert.pem", ssl_key_path="/etc/ssl/key.pem")
    assert "listen 443 ssl;" in text
    assert "return 301 https://$host$request_uri;" in text
    assert "ssl_certificate /etc/ssl/cert.pem;" in text
    assert "ssl_certificate_key /etc/ssl/key.pem;" in text
    assert "proxy_pass https://10.0.0.5:8443;" in text
    assert "proxy_ssl_server_name on;" in text

def test_static_root():
    text = render_site(name="static", server_name="static.example.com", root="/var/www/static")
    assert "root /var/www/static;" in text
    assert "proxy_pass" not in text


def test_custom_tls_port_redirect_and_site_overrides():
    text = render_site(name="ports", server_name="ports.example.com",
                       proxy_pass="http://127.0.0.1:9000", listen_port=8080,
                       ssl_enabled=True, ssl_port=8443,
                       ssl_cert_path="/etc/ssl/cert.pem", ssl_key_path="/etc/ssl/key.pem",
                       client_max_body_size="32M", proxy_read_timeout="300s")
    assert "listen 8080;" in text
    assert "listen 8443 ssl;" in text
    assert "return 301 https://$host:8443$request_uri;" in text
    assert "client_max_body_size 32M;" in text
    assert "proxy_read_timeout 300s;" in text


def test_proxy_map_is_namespaced():
    text = ENV.get_template("websocket_map.conf.j2").render(ansible_managed="test")
    assert "map $http_upgrade $nginx_setup_connection_upgrade" in text
    assert "''      close;" in text


def test_missing_tls_certificate_is_not_silently_rendered():
    import pytest
    from jinja2 import UndefinedError
    with pytest.raises(UndefinedError):
        render_site(name="bad", server_name="bad.example.com",
                    proxy_pass="http://127.0.0.1:9000", ssl_enabled=True)
