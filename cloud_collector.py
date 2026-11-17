import asyncio
import csv
import json
import os
import threading
from datetime import datetime, timezone

import websockets

DERIV_WS_URL = "wss://api.derivws.com/trading/v1/options/ws/public"
SYMBOL = "R_100"
CSV_FILE = os.environ.get("CSV_FILE", "tick_history.csv")

_lock = threading.Lock()
_started = False

_status = {
    "status": "STARTING",
    "symbol": SYMBOL,
    "ticks_received": 0,
    "last_price": None,
    "last_digit": None,
    "last_tick": None,
    "last_error": None,
}


def get_status():
    with _lock:
        return dict(_status)


def update_status(**values):
    with _lock:
        _status.update(values)


def save_tick(timestamp, price, digit):
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists or os.path.getsize(CSV_FILE) == 0:
            writer.writerow(["timestamp", "symbol", "price", "digit"])

        writer.writerow([timestamp, SYMBOL, price, digit])
        file.flush()


async def collect_forever():
    while True:
        update_status(status="CONNECTING", last_error=None)
        print(f"Connecting to Deriv for {SYMBOL}...", flush=True)

        try:
            async with websockets.connect(
                DERIV_WS_URL,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10,
            ) as ws:

                await ws.send(json.dumps({
                    "ticks": SYMBOL,
                    "subscribe": 1,
                }))

                update_status(status="CONNECTED")
                print("Deriv connection established.", flush=True)
                print("Waiting for Deriv subscription response and ticks...", flush=True)

                message_count = 0

                async for message in ws:
                    message_count += 1

                    if message_count <= 5:
                        print(
                            f"DERIV MESSAGE {message_count}: {message[:500]}",
                            flush=True,
                        )

                    response = json.loads(message)

                    if "error" in response:
                        raise RuntimeError(str(response["error"]))

                    if response.get("msg_type") != "tick":
                        continue

                    tick = response["tick"]
                    pip_size = int(tick.get("pip_size", 2))
                    price = f"{tick['quote']:.{pip_size}f}"
                    digit = int(price[-1])

                    timestamp = datetime.fromtimestamp(
                        tick["epoch"], timezone.utc
                    ).isoformat()

                    save_tick(timestamp, price, digit)

                    with _lock:
                        _status["status"] = "LIVE"
                        _status["ticks_received"] += 1
                        _status["last_price"] = price
                        _status["last_digit"] = digit
                        _status["last_tick"] = timestamp
                        _status["last_error"] = None

            print(
                f"Deriv connection closed normally after {message_count} messages.",
                flush=True,
            )

            update_status(
                status="RECONNECTING",
                last_error="Connection closed without an exception",
            )

        except Exception as error:
            update_status(
                status="RECONNECTING",
                last_error=str(error)[:250],
            )
            print(f"Deriv connection interrupted: {error}", flush=True)

        await asyncio.sleep(5)


def start_collector():
    global _started

    with _lock:
        if _started:
            return False
        _started = True

    thread = threading.Thread(
        target=lambda: asyncio.run(collect_forever()),
        name="deriv-cloud-collector",
        daemon=True,
    )
    thread.start()
    return True
