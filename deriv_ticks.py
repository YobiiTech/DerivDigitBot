
import asyncio
import json
import websockets
from datetime import datetime

DERIV_WS_URL = "wss://api.derivws.com/trading/v1/options/ws/public"

SYMBOL = "R_100"
MAX_TICKS = 20


async def collect_ticks():

    print("Connecting to Deriv...")

    try:
        async with websockets.connect(DERIV_WS_URL) as ws:

            print("Connected successfully!")
            print(f"Subscribing to {SYMBOL}...\n")

            request = {
                "ticks": SYMBOL,
                "subscribe": 1,
                "req_id": 2
            }

            await ws.send(json.dumps(request))

            count = 0

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

                    digits = price.replace(".", "")

                    last_digit = int(digits[-1])

                    count += 1

                    timestamp = datetime.now().strftime(
                        "%H:%M:%S"
                    )

                    print(
                        f"Tick {count:02d} | "
                        f"Time: {timestamp} | "
                        f"Price: {price} | "
                        f"Last digit: {last_digit}"
                    )

                    if count >= MAX_TICKS:
                        print("\nSuccessfully collected 20 ticks!")
                        break

    except Exception as error:
        print("Connection error:", error)


asyncio.run(collect_ticks())
