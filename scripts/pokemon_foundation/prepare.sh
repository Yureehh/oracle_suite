#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
checkout="$root/tmp/pokemon-foundation/showdown"
revision=3a766f2cfb5e51c1e428cfe87d0dba91a8f01640
if [ ! -d "$checkout/.git" ]; then
  mkdir -p "$checkout"
  git -C "$checkout" init
  git -C "$checkout" remote add origin https://github.com/smogon/pokemon-showdown.git
  git -C "$checkout" fetch --depth=1 origin "$revision"
  git -C "$checkout" checkout --detach "$revision"
fi
[ "$(git -C "$checkout" rev-parse HEAD)" = "$revision" ]
cmp "$checkout/package-lock.json" "$root/scripts/pokemon_foundation/showdown-package-lock.json"
cd "$checkout"
npm ci --omit=optional
node build
# Development configuration, not an upstream source patch. Local guests only.
cat > config/config.js <<'JS'
exports.port = 8765;
exports.bindaddress = '127.0.0.1';
exports.noipchecks = true;
exports.noguestsecurity = true;
exports.watchconfig = false;
exports.loginserver = 'http://127.0.0.1:8765/';
exports.subprocesses = {network: 1, simulator: 1, validator: 1, verifier: 1, localartemis: 0, remoteartemis: 0};
JS
uv sync --project "$root/scripts/pokemon_foundation" --locked
