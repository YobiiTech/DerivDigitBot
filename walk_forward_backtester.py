import csv
from collections import Counter, defaultdict

CSV_FILE = "tick_history.csv"
SYMBOL = "R_100"
INITIAL_TRAIN_PERCENT = 0.50
FOLDS = 5

digits = []

print("\nDERIV WALK-FORWARD BACKTESTER V1")
print("=" * 45)

with open(CSV_FILE, "r", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        try:
            if row["symbol"] != SYMBOL:
                continue

            digit = int(row["digit"])

            if 0 <= digit <= 9:
                digits.append(digit)

        except (ValueError, KeyError):
            continue

total = len(digits)

print(f"Symbol: {SYMBOL}")
print(f"Historical observations: {total}")

initial_train = int(total * INITIAL_TRAIN_PERCENT)
remaining = total - initial_train
block_size = remaining // FOLDS

if total < 1000 or block_size < 50:
    print("Collect more data before testing.")
    raise SystemExit

strategy_hits = 0
majority_hits = 0
repeat_hits = 0
total_tested = 0

for fold in range(FOLDS):

    start = initial_train + fold * block_size

    end = (
        total
        if fold == FOLDS - 1
        else start + block_size
    )

    training = digits[:start]

    transitions = defaultdict(Counter)

    for previous, following in zip(
        training[:-1], training[1:]
    ):
        transitions[previous][following] += 1

    global_prediction = Counter(
        training[1:]
    ).most_common(1)[0][0]

    fold_strategy = 0
    fold_majority = 0
    fold_repeat = 0

    for index in range(start, end):

        previous = digits[index - 1]
        actual = digits[index]

        if previous in transitions:
            prediction = transitions[
                previous
            ].most_common(1)[0][0]
        else:
            prediction = global_prediction

        fold_strategy += prediction == actual
        fold_majority += global_prediction == actual
        fold_repeat += previous == actual

    tested = end - start

    strategy_hits += fold_strategy
    majority_hits += fold_majority
    repeat_hits += fold_repeat
    total_tested += tested

    print(f"\nFOLD {fold + 1}")
    print("-" * 35)
    print(f"Training observations: {start}")
    print(f"Testing observations: {tested}")
    print(f"Transition accuracy: {fold_strategy/tested*100:.2f}%")
    print(f"Majority accuracy: {fold_majority/tested*100:.2f}%")
    print(f"Repeat accuracy: {fold_repeat/tested*100:.2f}%")

print("\n" + "=" * 45)
print("OVERALL WALK-FORWARD RESULTS")
print("=" * 45)

strategy_rate = strategy_hits / total_tested * 100
majority_rate = majority_hits / total_tested * 100
repeat_rate = repeat_hits / total_tested * 100

print(f"Total test observations: {total_tested}")

print(
    f"\nTransition strategy: "
    f"{strategy_hits}/{total_tested} "
    f"({strategy_rate:.2f}%)"
)

print(
    f"Majority baseline: "
    f"{majority_hits}/{total_tested} "
    f"({majority_rate:.2f}%)"
)

print(
    f"Repeat baseline: "
    f"{repeat_hits}/{total_tested} "
    f"({repeat_rate:.2f}%)"
)

print("\nPERFORMANCE DIFFERENCE")
print(f"Transition vs majority: {strategy_rate-majority_rate:+.2f} pp")
print(f"Transition vs repeat: {strategy_rate-repeat_rate:+.2f} pp")
print(f"Transition vs 10% reference: {strategy_rate-10:+.2f} pp")

print("\nResearch testing only.")
print("No trading edge or profitability is established.")
