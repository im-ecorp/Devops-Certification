# Apache HTTP Server proxy labs

Two loopback-only Apache 2.4 proxy topics. These are **virtual-host snippets**, not complete `/etc/apache2/apache2.conf` replacements. No files in the system Apache configuration are changed.

```text
apache/
├── README.md
├── reverse-proxy/
│   ├── README.md
│   ├── basic/
│   │   ├── README.md
│   │   └── proxy.conf
│   └── advanced/
│       ├── README.md
│       └── proxy.conf
└── forward-proxy/
    ├── README.md
    └── proxy.conf
```

- [Reverse proxy](reverse-proxy/README.md): basic HTTP proxying and an advanced WebSocket/timeouts variant.
- [Forward proxy](forward-proxy/README.md): one restricted HTTP-only explicit proxy. It intentionally has no Basic/Advanced split.

## Prerequisites

Apache HTTP Server 2.4.47+ is recommended for the advanced WebSocket example. On Debian, `apache2`, `a2enmod`, and `apache2ctl` provide the server and module management. A local HTTP origin listening on `127.0.0.1:19001` is required for requests; the examples do not start or install one. All sample Apache listeners are loopback-only.

Required modules: `mod_proxy` and `mod_proxy_http`; `mod_proxy_connect` is **not needed** for these labs and must stay disabled for the forward proxy. The advanced reverse proxy uses WebSocket upgrade support in `mod_proxy_http` (Apache 2.4.47+).

To try a lab on your own Apache installation, review the chosen configuration and add its `Listen 127.0.0.1:<port>` and `<VirtualHost>` block to an isolated test instance or a reviewed site configuration. Enable the listed modules first. Do **not** copy a snippet over the server's primary config or enable `ProxyRequests On` in a public/default virtual host. Use one lab at a time. A real deployment needs separate access controls, TLS where appropriate, monitoring, and a review of destination policy.

Syntax-check against your own installed Apache configuration before any reload:

```bash
apache2ctl -t
```

These labs do not configure a system service, change firewall rules, or provide a public forward proxy. See each topic README for request examples and security constraints.

References: [Apache mod_proxy](https://httpd.apache.org/docs/2.4/mod/mod_proxy.html), [mod_proxy_http](https://httpd.apache.org/docs/2.4/mod/mod_proxy_http.html), [mod_proxy_connect](https://httpd.apache.org/docs/2.4/mod/mod_proxy_connect.html).
