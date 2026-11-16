import csv
from collections import Counter

CSV_FILE = "tick_history.csv"

digits = []

print("\nDERIV SEQUENCE ANALYZER")
print("Loading historical tick data...")

with open(CSV_FILE, "r", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        try:
            digits.append(int(row["digit"]))
        except (ValueError, KeyError):
            continue

if len(digits) < 2:
    print("Not enough data. Collect more ticks.")
    exit()

# Compare each digit with the next digit
transitions = list(zip(digits[:-1], digits[1:]))

total = len(transitions)
pair_counts = Counter(transitions)

# Count consecutive repeated digits
repeats = sum(1 for first, second in transitions if first == second)

repeat_percentage = (repeats / total) * 100
expected_repeats = total * 0.10

print("\n========================================")
print("SEQUENCE SUMMARY")
print("========================================")

print(f"Total ticks: {len(digits)}")
print(f"Digit transitions: {total}")
print(f"Consecutive repeated digits: {repeats}")
print(f"Observed repeat rate: {repeat_percentage:.2f}%")
print(f"Expected repeats at 10% baseline: {expected_repeats:.1f}")

print("\n========================================")
print("10 MOST COMMON CONSECUTIVE PAIRS")
print("========================================")

for (first, second), count in pair_counts.most_common(10):
    percentage = (count / total) * 100
    print(f"{first} -> {second}: {count} times ({percentage:.2f}%)")

print("\nAnalysis complete.")
print("These are historical observations, not predictions.")


