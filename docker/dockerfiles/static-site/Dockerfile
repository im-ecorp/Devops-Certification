# syntax=docker/dockerfile:1
# This maintained NGINX variant already runs as a non-root user on port 8080.
FROM nginxinc/nginx-unprivileged:1.28-alpine
COPY site/ /usr/share/nginx/html/
EXPOSE 8080
# Inherit the base image's ENTRYPOINT and foreground NGINX CMD.
