
import asyncio
import csv
import json
import os
from datetime import datetime, timezone
from collections import Counter

import websockets

DERIV_WS_URL = "wss://api.derivws.com/trading/v1/options/ws/public"

SYMBOL = "R_100"
MAX_TICKS = 5000
CSV_FILE = "tick_history.csv"

digit_history = []


def save_tick(timestamp, symbol, price, digit):
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists or os.path.getsize(CSV_FILE) == 0:
            writer.writerow([
                "timestamp",
                "symbol",
                "price",
                "digit"
            ])

        writer.writerow([
            timestamp,
            symbol,
            price,
            digit
        ])


async def analyse_digits():

    while len(digit_history) < MAX_TICKS:

        print("\nConnecting to Deriv...")

        try:
            async with websockets.connect(
                DERIV_WS_URL,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10
            ) as ws:

                print("Connected successfully!")

                await ws.send(json.dumps({
                    "ticks": SYMBOL,
                    "subscribe": 1
                }))

                print(f"Collecting ticks from {SYMBOL}...")

                async for message in ws:
                    response = json.loads(message)

                    if "error" in response:
                        print("API Error:", response["error"])
                        break

                    if response.get("msg_type") == "tick":

                        tick = response["tick"]

                        quote = tick["quote"]
                        pip_size = int(tick.get("pip_size", 2))

                        price = f"{quote:.{pip_size}f}"
                        digit = int(price[-1])

                        timestamp = datetime.fromtimestamp(
                            tick["epoch"],
                            timezone.utc
                        ).isoformat()

                        save_tick(
                            timestamp,
                            SYMBOL,
                            price,
                            digit
                        )

                        digit_history.append(digit)

                        print(
                            f"Tick {len(digit_history):03d} | "
                            f"Price: {price} | "
                            f"Digit: {digit} | Saved to CSV"
                        )

                        if len(digit_history) >= MAX_TICKS:
                            break

        except Exception as error:
            print("Connection interrupted:", error)

        if len(digit_history) < MAX_TICKS:
            print(
                f"Progress: {len(digit_history)}/"
                f"{MAX_TICKS} ticks."
            )
            print("Reconnecting in 3 seconds...")
            await asyncio.sleep(3)

    counts = Counter(digit_history)

    print("\n========== DIGIT ANALYSIS ==========")

    for digit in range(10):
        frequency = counts[digit]
        percentage = frequency / len(digit_history) * 100

        print(
            f"Digit {digit}: {frequency} occurrences "
            f"({percentage:.2f}%)"
        )

    print("\nTotal ticks analysed:", len(digit_history))
    print("CSV file:", CSV_FILE)
    print("====================================")


asyncio.run(analyse_digits())
