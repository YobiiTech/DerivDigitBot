

import asyncio
import json
import websockets

DERIV_WS_URL = "wss://api.derivws.com/trading/v1/options/ws/public"


async def connect_to_deriv():
    print("Connecting to Deriv...")

    try:
        async with websockets.connect(DERIV_WS_URL) as ws:
            print("Successfully connected to Deriv!")

            request = {
                "active_symbols": "brief",
                "req_id": 1
            }

            await ws.send(json.dumps(request))
            print("Requesting available markets...\n")

            async for message in ws:
                response = json.loads(message)

                if "error" in response:
                    print("Deriv API error:", response["error"])
                    break

                if response.get("msg_type") == "active_symbols":
                    markets = response.get("active_symbols", [])

                    print("Markets returned:", len(markets))

                    for market in markets:
                        name = market.get(
                            "underlying_symbol_name",
                            market.get("display_name", "")
                        )

                        symbol = market.get(
                            "underlying_symbol",
                            market.get("symbol", "")
                        )

                        if "volatility 100" in name.lower():
                            print("Market:", name)
                            print("Symbol:", symbol)
                            print("-" * 35)

                    break

    except Exception as error:
        print("Connection failed:", error)


asyncio.run(connect_to_deriv())
