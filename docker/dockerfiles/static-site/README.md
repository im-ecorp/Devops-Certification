# Static website: HTML, CSS, and JavaScript

Scenario: serve a small page with NGINX. No Node.js, npm, or Python is needed inside
this image. NGINX serves files; JavaScript executes in the visitor's browser.

## Files and instructions

| File or instruction | Purpose |
| --- | --- |
| `site/index.html` | Page structure with a button and accessible result text. |
| `site/style.css` | Basic styling. |
| `site/script.js` | Updates the text when the button is clicked. |
| `FROM nginxinc/nginx-unprivileged:1.28-alpine` | Maintained non-root NGINX variant, listening on 8080. This is an NGINX project image, not the Docker Official `nginx` image. |
| `COPY site/ /usr/share/nginx/html/` | Copies only the site's files into the default web root. |
| `EXPOSE 8080` | Documents the port; the `-p` flag publishes it. |
| Inherited `ENTRYPOINT` and `CMD` | Use the base image's startup configuration and run NGINX in the foreground. |
| `.dockerignore` | Allowlist: only the site and Docker build configuration enter the context. |

The stock NGINX configuration is enough for these three files. No custom config is
needed. The example does not add SPA routing or TLS.

## Build and run

Prerequisites: Docker with a running daemon; `curl` for checks. From the repository root:

```bash
cd docker/dockerfiles/static-site
docker build -t learn-static-site .
docker run --rm -p 127.0.0.1:8080:8080 learn-static-site
```

Open <http://127.0.0.1:8080/> and click **Say hello**.
Expected result: `Hello from JavaScript!`.

In another terminal:

```bash
curl -f http://127.0.0.1:8080/
curl -f http://127.0.0.1:8080/style.css
curl -f http://127.0.0.1:8080/script.js
```

Optional configuration check after building:

```bash
docker run --rm learn-static-site nginx -t
```

Stop the server with Ctrl+C. `--rm` removes the disposable container.

## Try it and test

Change a heading or color and rebuild. Container contents do not automatically
follow local edits. For a fast local check, run this from the example directory
with Node.js installed on the host:

```bash
node test_site.cjs
```

This checks file references and JavaScript behavior; it does not replace a browser
or NGINX container test.

[Back to examples](../README.md)
