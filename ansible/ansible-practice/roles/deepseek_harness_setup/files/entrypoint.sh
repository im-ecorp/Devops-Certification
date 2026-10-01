#!/bin/sh
# Installs dsh into the home volume (the node image ships without it), then
# serves it. dsh binds loopback only, so a small forwarder exposes it to Traefik.
set -eu

runtime="$HOME/.dsh-runtime"
bin="$runtime/node_modules/@deepseek-ai/dsh/lib/bin.js"
installed=$(node -p "require('$runtime/node_modules/@deepseek-ai/dsh/package.json').version" 2>/dev/null || true)
wanted=$(npm view "@deepseek-ai/dsh@$DSH_VERSION" version 2>/dev/null | tail -1 || true)
if [ ! -f "$bin" ] || { [ -n "$wanted" ] && [ "$installed" != "$wanted" ]; }; then
  npm install --prefix "$runtime" --no-audit --no-fund "@deepseek-ai/dsh@$DSH_VERSION"
fi

node -e "
const net = require('net');
net.createServer((c) => {
  const u = net.connect(3080, '127.0.0.1');
  c.pipe(u).pipe(c);
  c.on('error', () => u.destroy());
  u.on('error', () => c.destroy());
}).listen(Number(process.env.DSH_PORT), '0.0.0.0');
" &

exec node --expose-internals "$bin" web \
  --no-open \
  --port 3080 \
  --trusted-host "$DSH_DOMAIN"
