
import csv
from collections import Counter

CSV_FILE = "tick_history.csv"
DIGITS = range(10)
SIGNIFICANCE_LEVEL = 0.05


def load_digits():

    digit_history = []

    with open(CSV_FILE, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            digit = int(row["digit"])

            if digit in DIGITS:
                digit_history.append(digit)

    return digit_history


def chi_square_test(observed, expected):

    return sum(
        (value - expected) ** 2 / expected
        for value in observed
    )


def analyse():

    try:
        digits = load_digits()
    except FileNotFoundError:
        print("Error: tick_history.csv not found.")
        return
    except (ValueError, KeyError) as error:
        print("Error reading CSV:", error)
        return

    total = len(digits)

    if total == 0:
        print("No valid digit records found.")
        return

    counts = Counter(digits)

    expected = total / 10

    observed = [counts[digit] for digit in DIGITS]

    chi_square = chi_square_test(observed, expected)

    # 9 degrees of freedom, 5% significance level.
    critical_value = 16.919

    print("\n========== STATISTICAL TEST ==========")

    print("Total observations:", total)
    print("Expected frequency per digit:", expected)

    print("\nObserved versus expected:")

    for digit in DIGITS:
        difference = counts[digit] - expected

        print(
            f"Digit {digit}: Observed={counts[digit]}, "
            f"Expected={expected:.1f}, "
            f"Difference={difference:+.1f}"
        )

    print("\nChi-square statistic:", round(chi_square, 4))
    print("Critical value:", critical_value)
    print("Significance level:", "5%")

    print("\nInterpretation:")

    if chi_square > critical_value:
        print(
            "The sample shows statistically significant "
            "evidence of deviation from a uniform distribution."
        )
    else:
        print(
            "The sample does not show statistically significant "
            "evidence of deviation from a uniform distribution."
        )

    print("\nImportant:")
    print("This test does not predict the next digit.")
    print("Statistical deviation does not prove a trading edge.")

    print("======================================")


if __name__ == "__main__":
    analyse()
