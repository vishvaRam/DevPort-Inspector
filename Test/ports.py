import socket
import sys
import threading
import time

# List any dummy test ports you want to bind
TEST_PORTS = [4000, 4001, 7070, 9999]


def run_dummy_server(port: int, stop_event: threading.Event):
    """Binds a TCP port and keeps it in LISTEN state."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow quick rebinding without TIME_WAIT errors
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind(("127.0.0.1", port))
        server.listen(5)
        server.settimeout(1.0)
        print(f"[+] Dummy server listening on port: {port}")

        while not stop_event.is_set():
            try:
                conn, _ = server.accept()
                conn.close()
            except socket.timeout:
                continue
            except OSError:
                break
    except Exception as e:
        print(f"[-] Could not bind to port {port}: {e}")
    finally:
        server.close()


def main():
    stop_event = threading.Event()
    threads = []

    print("Starting test dummy servers (Press Ctrl+C to stop)...")

    for port in TEST_PORTS:
        t = threading.Thread(
            target=run_dummy_server, args=(port, stop_event), daemon=True
        )
        t.start()
        threads.append(t)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping dummy servers...")
        stop_event.set()
        for t in threads:
            t.join(timeout=1.0)
        print("All test servers shut down.")
        sys.exit(0)


if __name__ == "__main__":
    main()