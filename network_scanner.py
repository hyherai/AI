import socket
import threading
import time

def check_port(host, port):
    """Attempts to establish a socket connection to the specified host and port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def scan_ports(host, ports):
    """Scans the provided list of ports on the specified host using threading for speed."""
    results = []
    threads = []

    for port in ports:
        t = threading.Thread(target=lambda: results.append(check_port(host, port)), args=(port,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # Sort results by port number for readability
    results.sort(key=lambda x: x[0])

    return results

def main():
    """Main entry point for the network scanner."""
    host = '127.0.0.1'
    target_ports = [80, 443, 8080]

    print(f"[INFO] Scanning host: {host}")
    print(f"[INFO] Target Ports: {target_ports}")
    print("-" * 40)

    results = scan_ports(host, target_ports)

    for port, is_open in results:
        status = "[OPEN]" if is_open else "[CLOSED]"
        print(f"[RESULT] Port {port}: {status}")

    open_count = sum(1 for _, is_open in results if is_open)
    print("-" * 40)
    print(f"[STATUS] Found {open_count} open port(s) out of {len(target_ports)}")

if __name__ == "__main__":
    main()
