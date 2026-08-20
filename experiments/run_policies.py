"""Policy mechanism comparison (Figure 4 of the paper)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import population
import policies


def main():
    pop = population.build_population()
    df = policies.run_all(pop)
    os.makedirs("results", exist_ok=True)
    df.to_csv("results/policy_comparison.csv", index=False)
    with __import__("pandas").option_context("display.width", 120):
        print(df.assign(federal_cost=lambda d: (d.federal_cost / 1e6).round(0))
                .rename(columns={"federal_cost": "federal_cost_$M"})
                .to_string(index=False))


if __name__ == "__main__":
    main()
