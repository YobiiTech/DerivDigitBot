import csv
from collections import Counter

CSV_FILE = "tick_history.csv"
SYMBOL = "R_100"
SEGMENTS = 5
CRITICAL_VALUE = 16.919

digits = []
timestamps = []

with open(CSV_FILE, "r", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        try:
            if row["symbol"] == SYMBOL:
                digit = int(row["digit"])

                if 0 <= digit <= 9:
                    digits.append(digit)
                    timestamps.append(row["timestamp"])
        except (ValueError, KeyError):
            continue

total = len(digits)

print("\nDERIV HISTORICAL STABILITY ANALYZER")
print("=" * 45)
print(f"Total valid ticks: {total}")

if total < 500:
    print("Not enough data. Collect at least 500 ticks.")
    raise SystemExit

segment_size = total // SEGMENTS
results = []

for i in range(SEGMENTS):
    start = i * segment_size
    end = total if i == SEGMENTS - 1 else (i + 1) * segment_size

    section = digits[start:end]
    section_times = timestamps[start:end]
    counts = Counter(section)

    expected = len(section) / 10
    chi_square = sum(
        (counts.get(d, 0) - expected) ** 2 / expected
        for d in range(10)
    )

    percentages = {
        d: counts.get(d, 0) / len(section) * 100
        for d in range(10)
    }

    results.append(percentages)

    print(f"\nSECTION {i + 1}")
    print("-" * 35)
    print(f"Ticks: {len(section)}")
    print(f"From: {section_times[0]}")
    print(f"To:   {section_times[-1]}")

    for d in range(10):
        print(f"Digit {d}: {percentages[d]:.2f}%")

    print(f"Chi-square: {chi_square:.4f}")

    if chi_square > CRITICAL_VALUE:
        print("Result: Significant deviation at 5% level")
    else:
        print("Result: No significant deviation at 5% level")

print("\nEARLIEST VS LATEST SECTION")
print("=" * 45)

changes = []

for d in range(10):
    change = results[-1][d] - results[0][d]
    changes.append((d, change))
    print(f"Digit {d}: {change:+.2f} percentage points")

changes.sort(key=lambda item: abs(item[1]), reverse=True)

print("\nLARGEST FREQUENCY CHANGES")
for digit, change in changes[:3]:
    print(f"Digit {digit}: {change:+.2f} percentage points")

print("\nResearch only — not a trade recommendation.")
