#!/bin/sh
set -eu
umask 077
# Compose bind-mounts these files: WordPress PHP-FPM must be able to read them.
# The parent directory is 0700 on the host; mounted files are 0444 in containers.
if ! command -v openssl >/dev/null 2>&1; then
  printf '%s\n' 'OpenSSL is required to generate passwords.' >&2
  exit 1
fi
if [ -L secrets ]; then
  printf '%s\n' 'Refusing to write through a symlinked secrets directory.' >&2
  exit 1
fi
if [ ! -d secrets ]; then
  mkdir -m 700 secrets
elif [ "$(stat -c '%a' secrets 2>/dev/null || stat -f '%Lp' secrets)" != 700 ]; then
  printf '%s\n' 'Existing secrets directory must be mode 0700; left unchanged.' >&2
  exit 1
fi
if [ -e secrets/db_password.txt ] || [ -e secrets/db_root_password.txt ] || \
   [ -L secrets/db_password.txt ] || [ -L secrets/db_root_password.txt ]; then
  if [ -s secrets/db_password.txt ] && [ -s secrets/db_root_password.txt ] && \
     [ ! -L secrets/db_password.txt ] && [ ! -L secrets/db_root_password.txt ]; then
    printf '%s\n' 'Existing secret files reused; no passwords or file permissions changed.'
    exit 0
  fi
  printf '%s\n' 'Incomplete secrets directory; inspect and repair manually. Nothing overwritten.' >&2
  exit 1
fi
(set -C; openssl rand -hex 32 > secrets/db_password.txt)
(set -C; openssl rand -hex 32 > secrets/db_root_password.txt)
chmod 444 secrets/db_password.txt secrets/db_root_password.txt
printf '%s\n' 'Two secret files created; host directory 0700, files 0444 for container readers.'
