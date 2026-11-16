
import csv
from collections import Counter

CSV_FILE = "tick_history.csv"
WINDOW = 100


def get_signal():
    digits = []

    try:
        with open(CSV_FILE, "r", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    digit = int(row["digit"])
                    if 0 <= digit <= 9:
                        digits.append(digit)
                except (ValueError, KeyError):
                    continue

    except FileNotFoundError:
        return {"status": "No historical data"}

    recent = digits[-WINDOW:]

    if len(recent) < WINDOW:
        return {
            "status": "Collecting data",
            "available": len(recent),
            "required": WINDOW
        }

    counts = Counter(recent)
    most = counts.most_common(1)[0][0]
    least = min(range(10), key=lambda d: counts[d])

    return {
        "status": "Analysis complete",
        "sample_size": len(recent),
        "most_frequent": most,
        "least_frequent": least,
        "frequencies": {
            digit: round(counts[digit] / len(recent) * 100, 2)
            for digit in range(10)
        },
        "signal": "OBSERVATION ONLY — NOT A TRADE RECOMMENDATION"
    }


if __name__ == "__main__":
    result = get_signal()

    print("\nDERIV LIVE SIGNAL ENGINE")
    print("========================")

    for key, value in result.items():
        print(f"{key}: {value}")
