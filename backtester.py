
import csv
from collections import Counter, defaultdict

CSV_FILE = "tick_history.csv"
TRAIN_PERCENTAGE = 0.70

digits = []

print("\nDERIV STRATEGY BACKTESTER — VERSION 2")
print("Loading historical data...")

with open(CSV_FILE, "r", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        try:
            digit = int(row["digit"])
            if 0 <= digit <= 9:
                digits.append(digit)
        except (ValueError, KeyError):
            continue

if len(digits) < 100:
    print("Collect at least 100 valid ticks.")
    raise SystemExit

split = int(len(digits) * TRAIN_PERCENTAGE)

training = digits[:split]
testing = digits[split:]

# Learn transitions from training data only.
successors = defaultdict(Counter)

for previous, following in zip(training[:-1], training[1:]):
    successors[previous][following] += 1

global_prediction = Counter(training[1:]).most_common(1)[0][0]

strategy_hits = 0
majority_hits = 0
tested = 0

# Track results for each previous digit.
state_results = defaultdict(lambda: [0, 0])

for previous, actual in zip(testing[:-1], testing[1:]):

    if previous in successors:
        prediction = successors[previous].most_common(1)[0][0]
    else:
        prediction = global_prediction

    strategy_hits += prediction == actual
    majority_hits += global_prediction == actual

    state_results[previous][1] += 1
    state_results[previous][0] += prediction == actual

    tested += 1

strategy_rate = strategy_hits / tested * 100
majority_rate = majority_hits / tested * 100

print("\n========== OVERALL RESULTS ==========")
print(f"Total ticks: {len(digits)}")
print(f"Training ticks: {len(training)}")
print(f"Testing transitions: {tested}")

print(f"\nTransition strategy: {strategy_hits}/{tested}")
print(f"Strategy accuracy: {strategy_rate:.2f}%")

print(f"\nMajority baseline: {majority_hits}/{tested}")
print(f"Majority accuracy: {majority_rate:.2f}%")

print("\nRandom guessing reference: 10.00%")

print("\n========== RESULTS BY PREVIOUS DIGIT ==========")

for digit in range(10):
    correct, count = state_results[digit]

    if count:
        accuracy = correct / count * 100
        print(
            f"After {digit}: {correct}/{count} correct "
            f"({accuracy:.2f}%)"
        )
    else:
        print(f"After {digit}: No test observations")

print("\n========== FINAL COMPARISON ==========")

print(f"Strategy vs majority: {strategy_rate - majority_rate:+.2f}")
print(f"Strategy vs random reference: {strategy_rate - 10:+.2f}")

print("\nHistorical prediction testing only.")
print("No profitability or future prediction is established.")
