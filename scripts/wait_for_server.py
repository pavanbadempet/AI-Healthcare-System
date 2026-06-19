import sys
import time

import requests


def wait_for_server(url="http://127.0.0.1:8000", timeout=60):
    print(f"Waiting for server at {url}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Server is up!")
                return True
        except requests.ConnectionError:
            pass
        time.sleep(1)
        print(".", end="", flush=True)

    print("\nServer failed to start within timeout.")
    return False

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    if not wait_for_server(url):
        sys.exit(1)
