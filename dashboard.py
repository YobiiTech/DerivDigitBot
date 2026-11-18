
import html
from collections import Counter, defaultdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import math

import storage

HOST = "127.0.0.1"
PORT = 8000
ANALYSIS_SYMBOL = "R_100"


def load_data():
    storage.init_db()
    return storage.load_ticks()


def frequency_table(digits):
    counts = Counter(digits)
    total = len(digits)

    rows = ""

    for digit in range(10):
        count = counts[digit]
        percentage = count / total * 100 if total else 0

        rows += f"""
        <tr>
            <td>{digit}</td>
            <td>{count}</td>
            <td>{percentage:.2f}%</td>
            <td>
                <div class="bar">
                    <div style="width:{percentage * 5}%"></div>
                </div>
            </td>
        </tr>
        """

    return rows

def signal_report(digits):
    recent = digits[-100:]

    if len(recent) < 100:
        return "<p>Waiting for 100 ticks...</p>"

    from collections import Counter

    counts = Counter(recent)
    rows = ""

    for digit in range(10):
        percentage = counts[digit] / 100 * 100
        rows += f"""
        <tr>
            <td>{digit}</td>
            <td>{counts[digit]}</td>
            <td>{percentage:.2f}%</td>
        </tr>
        """

    most = counts.most_common(1)[0][0]
    least = min(range(10), key=lambda d: counts[d])

    return f"""
    <p>Most frequent digit: <strong>{most}</strong></p>
    <p>Least frequent digit: <strong>{least}</strong></p>
    <p>Sample: Last 100 ticks</p>
    <table>
        <tr><th>Digit</th><th>Count</th><th>Frequency</th></tr>
        {rows}
    </table>
    <p class="warning">
        Historical observation only. No trade recommendation.
    </p>
    """


def rolling_report(digits):
    output = ""

    for size in [100, 500, 1000]:
        sample = digits[-size:]
        total = len(sample)
        counts = Counter(sample)

        if not total:
            continue

        most = counts.most_common(1)[0][0]
        least = min(range(10), key=lambda d: counts[d])

        output += f"""
        <tr>
            <td>Last {size}</td>
            <td>{total}</td>
            <td>{most}</td>
            <td>{least}</td>
        </tr>
        """

    return output


def sequence_report(digits):
    pairs = Counter(zip(digits[:-1], digits[1:]))
    transitions = max(len(digits) - 1, 0)

    repeats = sum(
        1 for a, b in zip(digits[:-1], digits[1:])
        if a == b
    )

    repeat_rate = repeats / transitions * 100 if transitions else 0

    rows = ""

    for (a, b), count in pairs.most_common(10):
        percentage = count / transitions * 100 if transitions else 0
        rows += f"<tr><td>{a} → {b}</td><td>{count}</td><td>{percentage:.2f}%</td></tr>"

    return rows, repeats, repeat_rate


def statistical_report(digits):
    total = len(digits)

    if total < 10:
        return "Insufficient data"

    counts = Counter(digits)
    expected = total / 10

    chi_square = sum(
        (counts[d] - expected) ** 2 / expected
        for d in range(10)
    )

    return f"{chi_square:.4f}"


def backtest(digits):
    if len(digits) < 100:
        return "Insufficient data", "Insufficient data", "Insufficient data"

    split = int(len(digits) * 0.70)
    training = digits[:split]
    testing = digits[split:]

    successors = defaultdict(Counter)

    for a, b in zip(training[:-1], training[1:]):
        successors[a][b] += 1

    baseline = Counter(training[1:]).most_common(1)[0][0]

    correct = 0
    baseline_correct = 0
    tested = 0

    for previous, actual in zip(testing[:-1], testing[1:]):
        prediction = (
            successors[previous].most_common(1)[0][0]
            if previous in successors else baseline
        )

        correct += prediction == actual
        baseline_correct += baseline == actual
        tested += 1

    if not tested:
        return "Insufficient data", "Insufficient data", "Insufficient data"

    strategy = correct / tested * 100
    benchmark = baseline_correct / tested * 100

    return (
        f"{strategy:.2f}%",
        f"{benchmark:.2f}%",
        f"{strategy - benchmark:+.2f} percentage points"
    )




def wilson_interval(hits, total):
    if not total:
        return 0.0, 0.0

    z = 1.96
    p = hits / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(
        p * (1 - p) / total + z * z / (4 * total * total)
    ) / denominator

    return max(0, centre - margin) * 100, min(1, centre + margin) * 100


def walk_forward_report(digits):
    if len(digits) < 100:
        return (
            '<tr><td colspan="6">Need at least 100 ticks.</td></tr>',
            {"transition": "Insufficient data", "majority": "—",
             "repeat": "—", "difference": "—", "confidence": "—"}
        )

    initial = len(digits) // 2
    remaining = len(digits) - initial

    totals = {"transition": 0, "majority": 0, "repeat": 0}
    tested = 0
    rows = ""

    for fold in range(5):
        start = initial + fold * remaining // 5
        end = initial + (fold + 1) * remaining // 5

        if end <= start:
            continue

        training = digits[:start]
        successors = defaultdict(Counter)

        for previous, following in zip(training[:-1], training[1:]):
            successors[previous][following] += 1

        global_prediction = Counter(training[1:]).most_common(1)[0][0]

        hits = {"transition": 0, "majority": 0, "repeat": 0}
        count = 0

        for index in range(start, end):
            previous = digits[index - 1]
            actual = digits[index]

            prediction = (
                successors[previous].most_common(1)[0][0]
                if previous in successors else global_prediction
            )

            hits["transition"] += prediction == actual
            hits["majority"] += global_prediction == actual
            hits["repeat"] += previous == actual
            count += 1

        tested += count

        for key in totals:
            totals[key] += hits[key]

        rows += (
            f"<tr><td>{fold + 1}</td><td>{start:,}</td>"
            f"<td>{count:,}</td>"
            f"<td>{hits['transition'] / count * 100:.2f}%</td>"
            f"<td>{hits['majority'] / count * 100:.2f}%</td>"
            f"<td>{hits['repeat'] / count * 100:.2f}%</td></tr>"
        )

    if not tested:
        return rows, {"transition": "—", "majority": "—",
                      "repeat": "—", "difference": "—", "confidence": "—"}

    transition = totals["transition"] / tested * 100
    majority = totals["majority"] / tested * 100
    repeat = totals["repeat"] / tested * 100
    low, high = wilson_interval(totals["transition"], tested)

    summary = {
        "transition": f"{transition:.2f}%",
        "majority": f"{majority:.2f}%",
        "repeat": f"{repeat:.2f}%",
        "difference": f"{transition - majority:+.2f} percentage points",
        "confidence": f"{low:.2f}% – {high:.2f}%"
    }

    return rows, summary


def stability_report(digits):
    if len(digits) < 250:
        message = '<tr><td colspan="4">Need at least 250 ticks.</td></tr>'
        return message, message

    total = len(digits)
    sections = [
        digits[i * total // 5:(i + 1) * total // 5]
        for i in range(5)
    ]

    rows = ""

    for index, section in enumerate(sections):
        counts = Counter(section)
        expected = len(section) / 10

        chi = sum(
            (counts[d] - expected) ** 2 / expected
            for d in range(10)
        )

        status = "No significant deviation" if chi < 16.919 else "Deviation detected"

        rows += (
            f"<tr><td>{index + 1}</td><td>{len(section):,}</td>"
            f"<td>{chi:.4f}</td><td>{status}</td></tr>"
        )

    first = Counter(sections[0])
    last = Counter(sections[-1])
    changes = ""

    for digit in range(10):
        first_pct = first[digit] / len(sections[0]) * 100
        last_pct = last[digit] / len(sections[-1]) * 100
        change = last_pct - first_pct

        changes += (
            f"<tr><td>{digit}</td><td>{first_pct:.2f}%</td>"
            f"<td>{last_pct:.2f}%</td><td>{change:+.2f} pp</td></tr>"
        )

    return rows, changes




def feed_health_report(records, digits):
    if not records:
        return {
            "status": "NO DATA",
            "age": "Unavailable",
            "rate": "0",
            "sample": "0",
            "distribution": "Insufficient data",
            "chi": "—"
        }

    try:
        latest_time = datetime.fromisoformat(records[-1]["timestamp"])

        if latest_time.tzinfo is None:
            latest_time = latest_time.replace(tzinfo=timezone.utc)

        age_seconds = max(
            0,
            (datetime.now(timezone.utc) -
             latest_time.astimezone(timezone.utc)).total_seconds()
        )
    except (ValueError, TypeError):
        age_seconds = None

    if age_seconds is None:
        status, age = "TIME ERROR", "Unknown"
    elif age_seconds <= 15:
        status, age = "LIVE", f"{age_seconds:.1f} seconds"
    elif age_seconds <= 60:
        status, age = "DELAYED", f"{age_seconds:.1f} seconds"
    else:
        status, age = "STALE", f"{age_seconds:.1f} seconds"

    recent_count = 0
    now = datetime.now(timezone.utc)

    for record in reversed(records):
        try:
            tick_time = datetime.fromisoformat(record["timestamp"])

            if tick_time.tzinfo is None:
                tick_time = tick_time.replace(tzinfo=timezone.utc)

            difference = (
                now - tick_time.astimezone(timezone.utc)
            ).total_seconds()

            if difference > 60:
                break

            if difference >= 0:
                recent_count += 1
        except (ValueError, TypeError):
            continue

    sample = digits[-500:]
    chi = "—"
    distribution = "Insufficient data"

    if len(sample) >= 100:
        counts = Counter(sample)
        expected = len(sample) / 10

        chi_value = sum(
            (counts[d] - expected) ** 2 / expected
            for d in range(10)
        )

        chi = f"{chi_value:.4f}"
        distribution = (
            "Unusual frequency variation"
            if chi_value >= 16.919
            else "Within reference threshold"
        )

    return {
        "status": status,
        "age": age,
        "rate": str(recent_count),
        "sample": f"{len(digits):,}",
        "distribution": distribution,
        "chi": chi
    }


def build_dashboard():
    records = [r for r in load_data() if r["symbol"] == ANALYSIS_SYMBOL]
    digits = [r["digit"] for r in records]

    total = len(digits)

    if records:
        latest = records[-1]
        latest_price = html.escape(str(latest["price"]))
        latest_symbol = html.escape(latest["symbol"])
        latest_time = html.escape(latest["timestamp"])
        latest_digit = latest["digit"]
    else:
        latest_price = "No data"
        latest_symbol = "Unknown"
        latest_time = "No data"
        latest_digit = "—"

    frequency = frequency_table(digits)
    signal = signal_report(digits)
    rolling = rolling_report(digits)

    pairs, repeats, repeat_rate = sequence_report(digits)

    chi_square = statistical_report(digits)

    walk_rows, walk_summary = walk_forward_report(digits)
    stability_rows, stability_changes = stability_report(digits)
    health = feed_health_report(records, digits)

    page = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="5">
<title>Deriv Digit Intelligence</title>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    padding: 24px;
    background: #101827;
    color: #f1f5f9;
    font-family: Arial, sans-serif;
}

header {
    margin-bottom: 25px;
}

h1 { margin-bottom: 5px; }

.subtitle { color: #94a3b8; }

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 15px;
}

.card, .panel {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 18px;
}

.metric {
    font-size: 27px;
    font-weight: bold;
    margin-top: 12px;
}

.small {
    color: #94a3b8;
    font-size: 13px;
}

h2 {
    font-size: 18px;
    margin-top: 0;
}

table {
    width: 100%;
    border-collapse: collapse;
}

td, th {
    padding: 10px;
    border-bottom: 1px solid #334155;
    text-align: left;
}

th { color: #94a3b8; }

.bar {
    background: #334155;
    height: 9px;
    border-radius: 8px;
    overflow: hidden;
}

.bar div {
    background: #38bdf8;
    height: 100%;
}

.warning {
    color: #fbbf24;
    line-height: 1.5;
}

.footer {
    color: #94a3b8;
    font-size: 12px;
    margin-top: 25px;
}

@media(max-width:600px) {
    body { padding: 12px; }
    .metric { font-size: 22px; }
}
</style>
</head>

<body>
<header>
    <h1>DERIV DIGIT INTELLIGENCE</h1>
    <div class="subtitle">
        Historical market research dashboard · Auto-refresh: 5 seconds
    </div>
</header>

<div class="grid">
    <div class="card">
        <div class="small">TOTAL TICKS</div>
        <div class="metric">TOTAL_VALUE</div>
    </div>

    <div class="card">
        <div class="small">LATEST PRICE</div>
        <div class="metric">PRICE_VALUE</div>
        <div class="small">SYMBOL_VALUE</div>
    </div>

    <div class="card">
        <div class="small">LATEST DIGIT</div>
        <div class="metric">DIGIT_VALUE</div>
    </div>

    <div class="card">
        <div class="small">REPEAT RATE</div>
        <div class="metric">REPEAT_VALUE</div>
    </div>
</div>


<div class="panel">
    <h2>Live Feed Health Monitor</h2>
    <div class="grid">
        <div class="card">
            <div class="small">FEED STATUS</div>
            <div class="metric">FEED_STATUS</div>
        </div>
        <div class="card">
            <div class="small">AGE OF LATEST TICK</div>
            <div class="metric">FEED_AGE</div>
        </div>
        <div class="card">
            <div class="small">TICKS IN LAST 60 SECONDS</div>
            <div class="metric">FEED_RATE</div>
        </div>
        <div class="card">
            <div class="small">VALID R_100 RECORDS</div>
            <div class="metric">FEED_SAMPLE</div>
        </div>
    </div>
    <h3>Recent Distribution Screening — Last 500 Ticks</h3>
    <p>Chi-square: FEED_CHI</p>
    <p>Screening result: FEED_DISTRIBUTION</p>
    <p class="warning">
        This is a monitoring threshold, not a prediction or trading signal.
        Consecutive ticks may not be statistically independent.
    </p>
</div>

<div class="panel">
    <h2>Digit Frequency — All Historical Ticks</h2>
    <table>
        <tr><th>Digit</th><th>Count</th><th>Frequency</th><th>Distribution</th></tr>
        FREQUENCY_ROWS
    </table>
</div>

<div class="panel">
    <h2>Live Signal Monitor</h2>
    SIGNAL_PANEL
    <p class="small">
        Observation only — not a trade recommendation.
    </p>
</div>
<div class="panel">
    <h2>Rolling Digit Analysis</h2>
    <table>
        <tr><th>Window</th><th>Available</th><th>Most frequent</th><th>Least frequent</th></tr>
        ROLLING_ROWS
    </table>
</div>

<div class="panel">
    <h2>Most Common Consecutive Pairs</h2>
    <table>
        <tr><th>Pair</th><th>Occurrences</th><th>Frequency</th></tr>
        PAIR_ROWS
    </table>
</div>

<div class="grid">
    <div class="card">
        <h2>Statistical Test</h2>
        <div class="small">Chi-square statistic</div>
        <div class="metric">CHI_VALUE</div>
        <p class="small">9 degrees of freedom · 5% critical value: 16.919</p>
    </div>

    <div class="card">
        <h2>Walk-Forward Evaluation</h2>
        <div class="small">Transition model accuracy</div>
        <div class="metric">WF_TRANSITION</div>
        <p class="small">Majority baseline: WF_MAJORITY</p>
        <p class="small">Repeat-digit baseline: WF_REPEAT</p>
        <p class="small">Model vs majority: WF_DIFFERENCE</p>
        <p class="small">95% confidence interval: WF_CONFIDENCE</p>
    </div>
</div>


<div class="panel">
    <h2>Five-Fold Walk-Forward Results</h2>
    <p class="small">Chronological testing. Each fold trains only on earlier observations.</p>
    <table>
        <tr><th>Fold</th><th>Training ticks</th><th>Test ticks</th>
        <th>Transition</th><th>Majority</th><th>Repeat</th></tr>
        WALK_FORWARD_ROWS
    </table>
</div>

<div class="panel">
    <h2>Historical Stability — Five Sections</h2>
    <p class="small">Chi-square critical value: 16.919 at 5% significance, 9 degrees of freedom.</p>
    <table>
        <tr><th>Section</th><th>Ticks</th><th>Chi-square</th><th>Result</th></tr>
        STABILITY_ROWS
    </table>
    <h3>First Section vs Last Section</h3>
    <table>
        <tr><th>Digit</th><th>First section</th><th>Last section</th><th>Change</th></tr>
        STABILITY_CHANGES
    </table>
</div>

<div class="panel">
    <h2>Latest Tick</h2>
    <p>Timestamp: TIME_VALUE</p>
    <p>Symbol: SYMBOL_VALUE</p>
    <p>Digit: DIGIT_VALUE</p>
</div>

<div class="panel">
    <h2>Research Disclaimer</h2>
    <p class="warning">
        Historical frequencies and backtest accuracy do not establish
        future predictability or profitability. Chi-square testing assumes
        independent observations, which consecutive market ticks may not be.
        This dashboard does not place trades.
    </p>
</div>

<div class="footer">
    DERIV DIGIT INTELLIGENCE · LOCAL RESEARCH APPLICATION
</div>
</body>
</html>
"""

    replacements = {
        "TOTAL_VALUE": str(total),
        "FEED_STATUS": health["status"],
        "FEED_AGE": health["age"],
        "FEED_RATE": health["rate"],
        "FEED_SAMPLE": health["sample"],
        "FEED_CHI": health["chi"],
        "FEED_DISTRIBUTION": health["distribution"],
        "PRICE_VALUE": latest_price,
        "SYMBOL_VALUE": latest_symbol,
        "DIGIT_VALUE": str(latest_digit),
        "REPEAT_VALUE": f"{repeat_rate:.2f}%",
        "FREQUENCY_ROWS": frequency,
        "ROLLING_ROWS": rolling,
        "PAIR_ROWS": pairs,
        "CHI_VALUE": str(chi_square),
        "WF_TRANSITION": walk_summary["transition"],
        "WF_MAJORITY": walk_summary["majority"],
        "WF_REPEAT": walk_summary["repeat"],
        "WF_DIFFERENCE": walk_summary["difference"],
        "WF_CONFIDENCE": walk_summary["confidence"],
        "WALK_FORWARD_ROWS": walk_rows,
        "STABILITY_ROWS": stability_rows,
        "STABILITY_CHANGES": stability_changes,
        "TIME_VALUE": latest_time,
        "SIGNAL_PANEL": signal,
    }

    for key, value in replacements.items():
        page = page.replace(key, value)

    return page


class DashboardHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return

        page = build_dashboard().encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), DashboardHandler)

    print("\n====================================")
    print("DERIV DIGIT INTELLIGENCE DASHBOARD")
    print("====================================")
    print(f"Dashboard running at http://{HOST}:{PORT}")
    print("Press CTRL+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
        server.server_close()
