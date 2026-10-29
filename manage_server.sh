#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

PID_FILE="$DIR/server.pid"
LOG_FILE="$DIR/server.log"
ICON="$DIR/static/workout-icon.svg"
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
  local lan_ip
  lan_ip=$(get_lan_ip)

  if pid=$(get_pid); then
    notify-send -i "$ICON" "Workout Helper Server" "Server is ALREADY running on port $PORT (PID $pid)!\nLocal: http://localhost:$PORT\nMobile: http://${lan_ip}:$PORT" 2>/dev/null || true
    echo "Workout Helper Server is ALREADY running on port $PORT (PID $pid)!"
    xdg-open "http://localhost:$PORT" >/dev/null 2>&1 &
    return 0
  fi

  echo "Starting Workout Helper Server on port $PORT..."
  if systemctl --user list-unit-files workout-helper.service >/dev/null 2>&1; then
    systemctl --user start workout-helper.service
  else
    setsid "$VENV_PY" server.py >> "$LOG_FILE" 2>&1 &
    local new_pid=$!
    echo "$new_pid" > "$PID_FILE"
  fi

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

  if [ $ready -eq 1 ]; then
    notify-send -i "$ICON" "Workout Helper Server" "Server Started Successfully! 🚀\nLocal: http://localhost:$PORT\nMobile: http://${lan_ip}:$PORT" 2>/dev/null || true
    echo "Server Started Successfully! 🚀"
    echo "Local:  http://localhost:$PORT"
    echo "Mobile: http://${lan_ip}:$PORT"
    xdg-open "http://localhost:$PORT" >/dev/null 2>&1 &
  else
    notify-send -i "$ICON" -u critical "Workout Helper Server" "Server started (PID $new_pid) but port $PORT is taking longer to respond. Check server.log." 2>/dev/null || true
    echo "Server started (PID $new_pid) but port $PORT is taking longer to respond. Check server.log."
  fi
}

stop_server() {
  local pid
  if pid=$(get_pid); then
    echo "Stopping Workout Helper Server (PID $pid)..."
    if systemctl --user is-active --quiet workout-helper.service; then
      systemctl --user stop workout-helper.service
    else
      kill "$pid" 2>/dev/null || true
      local count=0
      while kill -0 "$pid" 2>/dev/null && [ $count -lt 6 ]; do
        sleep 0.5
        count=$((count + 1))
      done
      if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null || true
      fi
    fi
    rm -f "$PID_FILE"
    notify-send -i "$ICON" "Workout Helper Server" "Server Stopped 🛑" 2>/dev/null || true
    echo "Server Stopped 🛑"
  else
    notify-send -i "$ICON" "Workout Helper Server" "Server is not currently running." 2>/dev/null || true
    echo "Server is not currently running."
  fi
}

restart_server() {
  if systemctl --user is-active --quiet workout-helper.service; then
    systemctl --user restart workout-helper.service
    sleep 1
    start_server
  else
    stop_server
    sleep 1
    start_server
  fi
}

view_logs() {
  if which mate-terminal >/dev/null 2>&1; then
    mate-terminal --title="Workout Helper Server Logs" -e "tail -f $LOG_FILE" &
  elif which x-terminal-emulator >/dev/null 2>&1; then
    x-terminal-emulator -e "tail -f $LOG_FILE" &
  else
    zenity --text-info --title="Workout Helper Server Logs" --filename="$LOG_FILE" --width=700 --height=500 &
  fi
}

gui_action() {
  local pid
  local lan_ip
  lan_ip=$(get_lan_ip)

  if pid=$(get_pid); then
    local action
    action=$(zenity --list \
      --title="Workout Helper Server (Active 🟢)" \
      --text="Server is RUNNING on PID $pid\n\n🌐 Local:   http://localhost:$PORT\n📱 Mobile:  http://${lan_ip}:$PORT\n\nSelect an action:" \
      --column="Action" \
      "🛑 Stop Server" \
      "🌐 Open Local Web App (Port 8081)" \
      "🚀 Open Live GitHub Pages Site" \
      "🔄 Restart Server" \
      "📋 View Server Logs" \
      --width=450 --height=340 2>/dev/null || true)

    case "$action" in
      "🛑 Stop Server")
        stop_server
        ;;
      "🌐 Open Local Web App (Port 8081)")
        xdg-open "http://localhost:$PORT" >/dev/null 2>&1 &
        ;;
      "🚀 Open Live GitHub Pages Site")
        xdg-open "https://imrugesh9.github.io/workout-helper/" >/dev/null 2>&1 &
        ;;
      "🔄 Restart Server")
        restart_server
        ;;
      "📋 View Server Logs")
        view_logs
        ;;
      *)
        exit 0
        ;;
    esac
  else
    start_server
  fi
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
    view_logs
    ;;
  *)
    gui_action
    ;;
esac
