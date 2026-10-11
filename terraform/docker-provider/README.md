# Docker Provider Labs

The Docker provider lets Terraform manage images, containers, networks, and volumes through an existing Docker daemon. It does not install Docker.

## WordPress

Both versions deploy WordPress and MariaDB on a dedicated network with persistent volumes. The database is internal; WordPress binds to localhost.

| Lab | Design | Default URL |
| --- | --- | --- |
| [Basic](wordpress/basic/README.md) | Direct resources and a supplied database password | http://localhost:8083 |
| [Advanced](wordpress/advanced/README.md) | Reusable module, generated passwords, and health checks | http://localhost:8080 |

1. Use Terraform >= 1.7 and < 2.0 and a reachable Docker daemon.
2. Start with basic, then compare the module wiring in advanced.
3. Run commands inside the selected version directory, not this parent. Each version has independent state and resource names.

Mock tests check configuration, not Docker or application readiness. State and saved plans contain database passwords. Destroying either lab removes its managed volumes and data; back up first. On a remote host, use an SSH tunnel for localhost access.

For a smaller first exercise, try the [Nginx container lab](../learn-terraform/docker-container/README.md).

[Back to Terraform practice](../README.md)
