#!/bin/sh
# Create local-only credentials once. Never replace an existing environment.
set -eu
cd "$(dirname "$0")/.."
umask 077
if [ -e .env ]; then
    printf '%s\n' '.env already exists; left unchanged.'
    exit 0
fi
command -v openssl >/dev/null 2>&1 || {
    printf '%s\n' 'openssl is required to generate credentials.' >&2
    exit 1
}
password=$(openssl rand -hex 32)
root_password=$(openssl rand -hex 32)
# noclobber protects against a concurrent invocation or dangling symlink.
set -C
{
    printf 'MYSQL_PASSWORD=%s\n' "$password"
    printf 'MYSQL_ROOT_PASSWORD=%s\n' "$root_password"
} > .env
printf '%s\n' 'Created .env (mode 0600). Keep this file with the database volume.'
