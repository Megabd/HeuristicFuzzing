"""Plot coverage growth for every CSV experiment in results/."""

import csv
from pathlib import Path

import matplotlib.pyplot as plt

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def load_runs():
    runs = []
    for path in sorted(RESULTS_DIR.glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))

        if not rows:
            continue

        rows.sort(key=lambda row: int(row["inputs"]))
        runs.append({
            "parser": rows[0]["parser"],
            "strategy": rows[0]["strategy"],
            "run_id": rows[0]["run_id"],
            "inputs": [int(row["inputs"]) for row in rows],
            "elapsed_seconds": [float(row["elapsed_seconds"]) for row in rows],
            "coverage_pct": [float(row["coverage_pct"]) for row in rows],
        })
    return runs


def plot(runs, x_column, x_label, output_name):
    parsers = sorted({run["parser"] for run in runs})
    fig, axes = plt.subplots(len(parsers), 1, figsize=(10, 4 * len(parsers)), squeeze=False)

    for ax, parser in zip(axes[:, 0], parsers):
        for run in runs:
            if run["parser"] != parser:
                continue

            # Include the run's time so repeated experiments stay distinguishable.
            label = f"{run['strategy']} ({run['run_id']})"
            ax.plot(run[x_column], run["coverage_pct"], marker=".", label=label)

        ax.set_title(parser.upper())
        ax.set_xlabel(x_label)
        ax.set_ylabel("Coverage (%)")
        ax.grid(alpha=0.3)
        ax.legend(fontsize="small")

    fig.tight_layout()
    output = RESULTS_DIR / output_name
    fig.savefig(output, dpi=150)
    print(f"Saved: {output}")


if __name__ == "__main__":
    runs = load_runs()
    if not runs:
        raise SystemExit("No experiment CSV files found in results/.")

    plot(runs, "inputs", "Number of inputs", "coverage_vs_inputs.png")
    plot(runs, "elapsed_seconds", "Elapsed execution time (s)", "coverage_vs_time.png")
    plt.show()
