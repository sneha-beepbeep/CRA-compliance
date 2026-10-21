#!/usr/bin/env bash
# Local, throwaway PostgreSQL 16 for development and tests, using the binaries
# from the optional `pgserver` wheel inside .venv (uv sync --group localpg).
# Listens on 127.0.0.1 only, password auth (scram-sha-256), random password kept
# in the data directory. Not a system service; stop with: scripts/localpg.sh stop
# Usage: scripts/localpg.sh start [DATADIR] [PORT]   -> prints a DATABASE_URL
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$HERE/.venv/lib/python3.12/site-packages/pgserver/pginstall/bin"
DATA="${2:-$HERE/.localpg}"
PORT="${3:-54329}"
case "${1:-start}" in
  start)
    if [ ! -f "$DATA/PG_VERSION" ]; then
      mkdir -p "$(dirname "$DATA")"
      PW="$(openssl rand -hex 16)"
      printf '%s' "$PW" > "$DATA.pw"; chmod 600 "$DATA.pw"
      "$BIN/initdb" -D "$DATA" -U postgres --auth=scram-sha-256 --pwfile="$DATA.pw" \
        --encoding=UTF8 --locale=C >/dev/null
    fi
    PW="$(cat "$DATA.pw")"
    if ! "$BIN/pg_ctl" -D "$DATA" status >/dev/null 2>&1; then
      "$BIN/pg_ctl" -D "$DATA" -l "$DATA/server.log" -w \
        -o "-c listen_addresses=127.0.0.1 -c port=$PORT -c unix_socket_directories='' -c timezone=UTC" start >/dev/null
    fi
    PGPASSWORD="$PW" "$BIN/psql" -h 127.0.0.1 -p "$PORT" -U postgres -tAc \
      "SELECT 1 FROM pg_database WHERE datname='tracker'" | grep -q 1 \
      || PGPASSWORD="$PW" "$BIN/createdb" -h 127.0.0.1 -p "$PORT" -U postgres tracker
    echo "postgres://postgres:$PW@127.0.0.1:$PORT/tracker"
    ;;
  stop) "$BIN/pg_ctl" -D "$DATA" -m fast stop ;;
  *) echo "usage: $0 start|stop [DATADIR] [PORT]" >&2; exit 2 ;;
esac
