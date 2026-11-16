
import csv
from collections import Counter

CSV_FILE = "tick_history.csv"


def analyse_history():

    digit_history = []

    try:
        with open(CSV_FILE, "r", newline="") as file:

            reader = csv.DictReader(file)

            for row in reader:
                digit = int(row["digit"])

                if 0 <= digit <= 9:
                    digit_history.append(digit)

    except FileNotFoundError:
        print("Error: CSV file not found!")
        return

    except (ValueError, KeyError) as error:
        print("Error reading CSV data:", error)
        return

    if not digit_history:
        print("No valid tick data found.")
        return

    counts = Counter(digit_history)

    print("\n========== HISTORICAL ANALYSIS ==========")

    print("Total historical ticks:", len(digit_history))

    print("\nDigit Frequency Report:")

    for digit in range(10):

        frequency = counts[digit]
        percentage = frequency / len(digit_history) * 100

        print(
            f"Digit {digit}: {frequency} occurrences "
            f"({percentage:.2f}%)"
        )

    highest = max(counts.values())
    lowest = min(counts.values())

    most_common = [
        digit for digit in range(10)
        if counts[digit] == highest
    ]

    least_common = [
        digit for digit in range(10)
        if counts[digit] == lowest
    ]

    print("\nMost frequent digits:", most_common)
    print("Least frequent digits:", least_common)

    print("=========================================")


if __name__ == "__main__":
    analyse_history()
