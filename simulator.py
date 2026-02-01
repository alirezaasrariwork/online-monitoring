# signal_generator.py
import requests
import random
import time

API_URL = "http://localhost:8000"  # adjust if Docker uses another host

def send_signal(endpoint, value):
    try:
        r = requests.post(f"{API_URL}/{endpoint}", json={"value": value}, timeout=5)
        print(f"Sent {endpoint}={value}, response: {r.json()}")
    except Exception as e:
        print(f"Failed to send {endpoint}: {e}")

while True:
    # randomly pick a signal A/B/C
    endpoint = random.choice(["signal/a", "signal/b", "signal/c"])
    if endpoint == "signal/a":
        value = random.uniform(50, 100)  # Temperature
    elif endpoint == "signal/b":
        value = random.uniform(60, 130)  # Pressure
    else:
        value = random.uniform(1, 10)    # Vibration

    send_signal(endpoint, value)

    # random interval 2-4 seconds
    time.sleep(random.choice([20,30,40]))
