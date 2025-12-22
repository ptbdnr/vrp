import json
from pathlib import Path

from tabulate import tabulate

dataset_ids = [f"i{x}0" for x in range(2, 7)]
improvers = ["LocalSearchImprover", "SimulatedAnnealingImprover", "ALNSWrapper"]
results = []

for dataset_id in dataset_ids:
    for improver in improvers:
        iter_filepath = Path(f"doc/results/{dataset_id}/{improver}_iter.json")
        with iter_filepath.open("r", encoding="utf-8") as f:
            iters = json.load(f)
        keys = ["iteration", "best_value"]
        last_iter = {
            "dataset_id": dataset_id,
            "improver": improver,
            **{key: iters[-1][key] for key in keys},
        }
        results.append(last_iter)

print(tabulate(results, headers="keys", tablefmt="github", floatfmt=".2f"))
