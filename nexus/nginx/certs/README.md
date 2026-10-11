Place your CA-issued fullchain.pem and privkey.pem here before starting Nginx.
The certificate must cover repo, hub, quay, k8s, gcr, k8s-gcr, and github hostnames.
Use restrictive permissions for the private key. Certificates and keys are Git-ignored.
Renew certificates externally, then validate and reload Nginx; ACME is not bundled.
