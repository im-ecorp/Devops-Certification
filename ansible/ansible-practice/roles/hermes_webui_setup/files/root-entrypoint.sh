#!/bin/bash
# Managed by Ansible (hermes_webui_setup). Wraps the upstream entrypoint.
#
# The upstream init remaps the "hermeswebui" account to WANTED_UID and then
# recursively chowns its home. With a root-owned Hermes home (WANTED_UID=0) that
# creates a second root account and loops back into the root init branch.
#
# With HERMES_WEBUI_ROOT_HOME_MODE=1 this wrapper skips only that remap branch
# and runs the rest of the upstream entrypoint unchanged. Otherwise it runs the
# upstream entrypoint as-is. The patch must match exactly once, so an upstream
# change fails loudly instead of running with the wrong ownership.
set -euo pipefail

upstream_entrypoint=/hermeswebui_init.bash
patched_entrypoint=/tmp/hermeswebui_init-root-home.bash

if [ ! -r "${upstream_entrypoint}" ]; then
    echo "hermes-webui: ${upstream_entrypoint} is missing; the image layout changed." >&2
    exit 1
fi

if [ "${HERMES_WEBUI_ROOT_HOME_MODE:-0}" != "1" ]; then
    exec /bin/bash "${upstream_entrypoint}" "$@"
fi

python3 - "${upstream_entrypoint}" "${patched_entrypoint}" <<'PY'
import pathlib
import sys

source = pathlib.Path(sys.argv[1])
destination = pathlib.Path(sys.argv[2])
needle = 'if [ "A${whoami}" == "Aroot" ]; then'
replacement = (
    'if [ "A${whoami}" == "Aroot" ] '
    '&& [ "${HERMES_WEBUI_ROOT_HOME_MODE:-0}" != "1" ]; then'
)
text = source.read_text(encoding="utf-8")
if text.count(needle) != 1:
    raise SystemExit(
        "hermes-webui: expected exactly one upstream root-init marker; "
        "refusing to start"
    )
destination.write_text(text.replace(needle, replacement, 1), encoding="utf-8")
destination.chmod(0o700)
PY

exec "${patched_entrypoint}" "$@"
