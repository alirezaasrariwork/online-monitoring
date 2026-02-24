# signal_generator.py
import requests
import random
import time

API_URL = "http://localhost:8000"  # adjust if Docker uses another host

def send_signal(endpoint, payload):
    try:
        r = requests.post(f"{API_URL}/{endpoint}", json=payload, timeout=5)
        print(f"Sent {endpoint}={payload}, response: {r.json()}")
    except Exception as e:
        print(f"Failed to send {endpoint}: {e}")

while True:
    # randomly pick a signal A/B/C/DGA
    choice = random.choice(["signal/a", "signal/b", "signal/c", "signal/dga"])

    if choice == "signal/a":
        value = random.uniform(50, 100)  # Temperature
        payload = {"value": value}
    elif choice == "signal/b":
        value = random.uniform(60, 130)  # Pressure
        payload = {"value": value}
    elif choice == "signal/c":
        value = random.uniform(1, 10)    # Vibration
        payload = {"value": value}
    else:  # signal/dga
        # Random but somewhat realistic DGA ranges (you can tune these)
        payload = {
            "H2":  random.uniform(10, 500),
            "CH4": random.uniform(5, 400),
            "C2H6": random.uniform(1, 200),
            "C2H4": random.uniform(1, 300),
            "C2H2": random.uniform(0, 50),
            "CO":  random.uniform(50, 1500),
            "CO2": random.uniform(500, 5000),
        }

    send_signal(choice, payload)

    # random interval 20–40 seconds
    time.sleep(random.choice([20, 30, 40]))
