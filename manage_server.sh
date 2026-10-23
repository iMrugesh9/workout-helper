#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

PID_FILE="$DIR/server.pid"
LOG_FILE="$DIR/server.log"
PORT=8081
VENV_PY="$DIR/.venv/bin/python"

get_pid() {
  if [ -f "$PID_FILE" ]; then
    local p
    p=$(cat "$PID_FILE" 2>/dev/null || true)
    if [ -n "$p" ] && kill -0 "$p" 2>/dev/null && ps -p "$p" -o cmd= | grep -q "server\.py"; then
      echo "$p"
      return 0
    fi
  fi
  local p
  p=$(pgrep -f "workout.*server\.py" | head -n 1)
  if [ -n "$p" ]; then
    echo "$p"
    return 0
  fi
  return 1
}

get_lan_ip() {
  local ip
  ip=$(hostname -I 2>/dev/null | awk '{print $1}')
  if [ -z "$ip" ]; then
    ip="127.0.0.1"
  fi
  echo "$ip"
}

start_server() {
  local pid
  if pid=$(get_pid); then
    echo "Workout Helper Server is ALREADY running on port $PORT (PID $pid)!"
    xdg-open "http://localhost:$PORT" >/dev/null 2>&1 &
    return 0
  fi

  echo "Starting Workout Helper Server on port $PORT..."
  setsid "$VENV_PY" server.py >> "$LOG_FILE" 2>&1 &
  local new_pid=$!
  echo "$new_pid" > "$PID_FILE"

  local count=0
  local ready=0
  while [ $count -lt 12 ]; do
    if curl -s -m 1 "http://localhost:$PORT" >/dev/null 2>&1; then
      ready=1
      break
    fi
    sleep 0.5
    count=$((count + 1))
  done

  local lan_ip
  lan_ip=$(get_lan_ip)
  if [ $ready -eq 1 ]; then
    echo "Server Started Successfully! 🚀"
    echo "Local:  http://localhost:$PORT"
    echo "Mobile: http://${lan_ip}:$PORT"
    xdg-open "http://localhost:$PORT" >/dev/null 2>&1 &
  else
    echo "Server started (PID $new_pid) but port $PORT is taking longer to respond. Check server.log."
  fi
}

stop_server() {
  local pid
  if pid=$(get_pid); then
    echo "Stopping Workout Helper Server (PID $pid)..."
    kill "$pid" 2>/dev/null || true
    local count=0
    while kill -0 "$pid" 2>/dev/null && [ $count -lt 6 ]; do
      sleep 0.5
      count=$((count + 1))
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
    echo "Server Stopped 🛑"
  else
    echo "Server is not currently running."
  fi
}

restart_server() {
  stop_server
  sleep 1
  start_server
}

case "$1" in
  start)
    start_server
    ;;
  stop)
    stop_server
    ;;
  restart)
    restart_server
    ;;
  status)
    if pid=$(get_pid); then
      echo "Server is running on port $PORT (PID: $pid)"
    else
      echo "Server is stopped"
    fi
    ;;
  logs)
    tail -f "$LOG_FILE"
    ;;
  *)
    start_server
    ;;
esac
