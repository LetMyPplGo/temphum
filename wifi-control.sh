#!/bin/bash
set -e

CMD="$1"
SSID="$2"
PASS="$3"

case "$CMD" in
  ap)
    # Отключаем всё и включаем hotspot
    nmcli device disconnect wlan0 || true
    nmcli connection down Hotspot || true

    nmcli device wifi hotspot \
      ifname wlan0 \
      ssid "$SSID" \
      password "$PASS"
    ;;

  client)
    # Отключаем всё, гасим Hotspot
    nmcli device disconnect wlan0 || true
    nmcli connection down Hotspot || true

    CON_NAME="wifi-$SSID"

    # Чистим старый профиль, если был
    nmcli connection delete "$CON_NAME" || true

    # Создаём новый профиль
    nmcli connection add \
      type wifi \
      ifname wlan0 \
      con-name "$CON_NAME" \
      ssid "$SSID"

    # Настраиваем WPA-PSK
    nmcli connection modify "$CON_NAME" \
      wifi-sec.key-mgmt wpa-psk \
      wifi-sec.psk "$PASS"

    # Поднимаем соединение
    nmcli connection up "$CON_NAME"
    ;;

  ping)
    HOST="${SSID:-1.1.1.1}"   # тут SSID используется как HOST, если передан
    ping -c 1 -W 2 "$HOST"
    ;;

  *)
    echo "Usage: $0 ap <ssid> <pass> | client <ssid> <pass> | ping [host]" >&2
    exit 1
    ;;
esac
