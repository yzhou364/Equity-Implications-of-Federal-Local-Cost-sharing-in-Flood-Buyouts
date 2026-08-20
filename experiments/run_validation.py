"""Model validation against historical buyout programs (Table 2).

Each historical program is mapped to the model region with the most
similar housing-market and hazard profile, and evaluated under the
program's approximate effective terms (federal/state cost share and
subsidy generosity). Observed rates are completed-acquisition rates
among eligible households, from program documentation.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd

import population
import model

# program -> (model region, effective alpha, cap, observed rate)
PROGRAMS = {
    "Staten Island (Sandy)":   ("Staten Island", 1.00, 350_000, 0.082),
    "Harris County (Harvey)":  ("Houston",       0.90, 250_000, 0.045),
    "NJ Blue Acres":           ("Norfolk",       0.95, 250_000, 0.068),
    "Charlotte-Mecklenburg":   ("Charleston",    1.00, 300_000, 0.121),
}


def main():
    pop = population.build_population()
    rows = []
    for prog, (region, alpha, cap, observed) in PROGRAMS.items():
        sub = pop[pop.region == region].reset_index(drop=True)
        o = model.evaluate_policy(sub, alpha, cap=cap)
        predicted = (o.n_low + o.n_high) / len(sub)
        err = (predicted - observed) / observed
        rows.append((prog, region, alpha, observed, predicted, err))
        print(f"{prog:26s} observed={observed:.1%} predicted={predicted:.1%} "
              f"error={err:+.0%}")
    os.makedirs("results", exist_ok=True)
    pd.DataFrame(rows, columns=["program", "model_region", "alpha",
                                "observed", "predicted", "error"]) \
        .to_csv("results/validation.csv", index=False)


if __name__ == "__main__":
    main()
