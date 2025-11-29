import subprocess
import time


def run_cmd(args):
    """
    Запускаем системную команду.
    - Логируем саму команду.
    - В случае ошибки печатаем stdout/stderr и пробрасываем исключение дальше.
    """
    print("Running:", " ".join(args))
    try:
        result = subprocess.run(
            args,
            check=True,
            text=True,          # получаем строки, а не байты
            capture_output=True # захватываем stdout и stderr
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed with code {e.returncode}")
        if e.stdout:
            print("=== STDOUT ===")
            print(e.stdout)
        if e.stderr:
            print("=== STDERR ===")
            print(e.stderr)
        raise


def stop_all_wifi_connections():
    run_cmd(["nmcli", "device", "disconnect", "wlan0"])


def start_ap_mode(ssid="busbox", password="busboxBUSBOX"):
    # stop_all_wifi_connections()

    run_cmd([
        "nmcli", "device", "wifi", "hotspot",
        "ifname", "wlan0",
        "ssid", ssid,
        "password", password
    ])

    # По умолчанию создаётся connection с именем "Hotspot"
    print(f"AP mode ON: SSID={ssid}, password={password}")


def start_client_mode(ssid, password, connection_name=None):
    if connection_name is None:
        connection_name = f"wifi-{ssid}"

    # 1. На всякий случай разорвём все текущие подключения
    try:
        stop_all_wifi_connections()
    except subprocess.CalledProcessError:
        pass

    # 2. Пробуем погасить хотспот, если он есть
    try:
        run_cmd(["nmcli", "connection", "down", "Hotspot"])
    except subprocess.CalledProcessError:
        pass

    # 3. Удаляем старый профиль с таким именем (если есть),
    #    чтобы избежать "наследования" кривых настроек
    try:
        run_cmd(["nmcli", "connection", "delete", connection_name])
    except subprocess.CalledProcessError:
        pass

    # 4. Создаём новый профиль
    run_cmd([
        "nmcli", "connection", "add",
        "type", "wifi",
        "ifname", "wlan0",
        "con-name", connection_name,
        "ssid", ssid
    ])

    # 5. Настраиваем WPA-PSK
    run_cmd([
        "nmcli", "connection", "modify", connection_name,
        "wifi-sec.key-mgmt", "wpa-psk",
        "wifi-sec.psk", password
    ])

    # 6. Поднимаем соединение
    run_cmd([
        "nmcli", "connection", "up", connection_name
    ])

    print(f"Client mode ON: connected to SSID={ssid} (connection {connection_name})")


def wait_for_internet(timeout: int = 10,
                      host: str = "1.1.1.1") -> bool:
    """
    Ждёт до `timeout` секунд появления интернета, проверяя ping'ом.
    Возвращает True, если интернет появился, False — если вышел таймаут.

    timeout  - общий таймаут ожидания (секунды)
    host     - кого пингуем (по умолчанию 1.1.1.1 / Cloudflare)
    """
    start = time.time()

    while time.time() - start < timeout:
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", host],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if result.returncode == 0:
                print(f"Internet OK (ping {host} successful)")
                return True
            else:
                print(f"No internet yet (ping {host} failed)")
        except FileNotFoundError:
            print("ping command not found")
            return False

        time.sleep(2)

    print("Internet did not appear within timeout")
    return False

def connect_with_fallback(ssid, pwd):
    try:
        start_client_mode(ssid, pwd)
    except Exception as err:
        print(f'Failed to enable wifi\n{err}')
    if not wait_for_internet():
        print(f'Failed to connect to {ssid}, fallback to AP mode')
        start_ap_mode()


if __name__ == "__main__":
    print(wait_for_internet())

    # 1) Включить режим точки доступа:
    # start_ap_mode()

    # 2) Включить режим клиента:
    # start_client_mode("MyHomeWiFi", "SuperSecretPass")

    pass
