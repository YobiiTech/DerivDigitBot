
import csv
from collections import Counter

CSV_FILE = "tick_history.csv"
SYMBOL = "R_100"

def load_digits():
    digits = []

    with open(CSV_FILE, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["symbol"] == SYMBOL:
                digit = int(row["digit"])

                if 0 <= digit <= 9:
                    digits.append(digit)

    return digits


def analyze_window(digits, window_size):
    sample = digits[-window_size:]

    if not sample:
        print(f"\nNo data available for last {window_size} ticks.")
        return

    counts = Counter(sample)
    total = len(sample)

    print(f"\n{'=' * 40}")
    print(f"LAST {total} TICKS")
    print("=" * 40)

    for digit in range(10):
        count = counts.get(digit, 0)
        percentage = (count / total) * 100

        print(
            f"Digit {digit}: {count:4} occurrences "
            f"({percentage:5.2f}%)"
        )

    highest = max(counts.values())
    lowest = min(counts.get(d, 0) for d in range(10))

    most_common = [
        d for d in range(10) if counts.get(d, 0) == highest
    ]

    least_common = [
        d for d in range(10) if counts.get(d, 0) == lowest
    ]

    print(f"\nMost frequent: {most_common}")
    print(f"Least frequent: {least_common}")


def main():
    print("\nDERIV ROLLING DIGIT ANALYZER")
    print("Loading historical tick data...")

    digits = load_digits()

    print(f"Total ticks available: {len(digits)}")

    if not digits:
        print("No tick data found.")
        return

    for window in [100, 500, 1000]:
        analyze_window(digits, window)


if __name__ == "__main__":
    main()
