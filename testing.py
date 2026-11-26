
import io
import coverage
import csv
import time
import argparse
import random
from pathlib import Path
from datetime import datetime
from fuzzingbook.Grammars import trim_grammar
from fuzzingbook.MutationFuzzer import mutate

# Capture initialization coverage
import_cov = coverage.Coverage(
    source=["json5", "tomlkit", "toml_sort", "ruamel.yaml"],
    branch=True,
    data_file=None
)

import_cov.start()

from config import (
    SUT, SUT_CONFIG,
    Strategy, STRATEGY_CLASSES,
    DEFAULT_SUT, DEFAULT_STRATEGY,
    MAX_TESTS, MAX_NONTERMINALS,
    MUTATION_RATE, MAX_MUTATIONS
)

import_cov.stop()


def run_experiment(sut, strategy):
    grammar, parser, module, parser_file = SUT_CONFIG[sut]

    parser_files = (
    parser_file if isinstance(parser_file, list)
    else [parser_file]
    )

    generator = STRATEGY_CLASSES[strategy](
        trim_grammar(grammar),
        start_symbol="<start>",
        max_nonterminals=MAX_NONTERMINALS
    )

    # Coverage checkpoints
    checkpoints = {1, 5, 10, 25, 50, 100, MAX_TESTS}
    checkpoints.update(range(200, MAX_TESTS + 1, 100))

    cov = coverage.Coverage(include=parser_files, branch=True)

    cov.get_data().update(import_cov.get_data())
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    results = []
    accepted = rejected = crashes = 0
    total_time = 0.0
    mutated_count = 0
    
    for i in range(1, MAX_TESTS + 1):
        start_time = time.perf_counter()
        generated = generator.fuzz()

        # Occasionally mutate the grammar-generated input
        if random.random() < MUTATION_RATE:
            for _ in range(random.randint(1, MAX_MUTATIONS)):
                generated = mutate(generated)
            mutated_count += 1

        cov.start()
        try:
            parser(generated)
            accepted += 1

        except ValueError:
            rejected += 1

        except Exception:
            crashes += 1

        finally:
            cov.stop()
            total_time += time.perf_counter() - start_time

        if i in checkpoints:
            pct = cov.report(
                include=[parser_files],
                file=io.StringIO()
            )

            results.append({
                "run_id": run_id,
                "parser": sut.value,
                "strategy": strategy.value,
                "inputs": i,
                "coverage_pct": round(pct, 2),
                "elapsed_seconds": round(total_time, 4),
                "accepted": accepted,
                "rejected": rejected,
                "crashes": crashes,
                "mutated": mutated_count,
            })

    cov.save()

    # Export CSV
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)

    filename = output_dir / f"{run_id}_{sut.value}_{strategy.value}.csv"

    with filename.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"{sut.value} / {strategy.value}:")
    print(f"  Coverage: {pct:.2f}% | Time: {total_time:.3f}s")
    print(f"  Accepted: {accepted} | Rejected: {rejected} | Crashes: {crashes}")
    print(f"  Saved: {filename}\n")


# PowerShell arguments
if __name__ == "__main__":
    cli = argparse.ArgumentParser()

    cli.add_argument(
        "sut",
        nargs="?",
        type=str.lower,
        choices=[s.value for s in SUT] + ["all"],
        default=DEFAULT_SUT.value
    )

    cli.add_argument(
        "strategy",
        nargs="?",
        type=str.lower,
        choices=[s.value for s in Strategy] + ["all"],
        default=None
    )

    args = cli.parse_args()

    # Select parsers
    suts = list(SUT) if args.sut == "all" else [SUT(args.sut)]

    # Select strategies
    if args.strategy == "all" or (args.sut == "all" and args.strategy is None):
        strategies = list(Strategy)
    else:
        strategies = [Strategy(args.strategy or DEFAULT_STRATEGY.value)]

    # Run selected combinations
    for sut in suts:
        for strategy in strategies:
            run_experiment(sut, strategy)
