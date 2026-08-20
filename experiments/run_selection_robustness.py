"""Equilibrium-selection robustness check (Supplementary Materials S3.5).

When a jurisdiction's subsidy problem admits multiple cost-minimizing
candidates, the baseline solver selects the lowest-subsidy optimum.
This script recomputes the full alpha sweep under the opposite
(highest-subsidy) selection rule and reports any differences in the
equilibrium outcomes (RRG, relocations, federal cost, participation).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

import population
import model


def main():
    pop = population.build_population()
    lo = model.sweep_alpha(pop, selection="lowest")
    hi = model.sweep_alpha(pop, selection="highest")

    diff = (lo.set_index("alpha") - hi.set_index("alpha")).abs()
    os.makedirs("results", exist_ok=True)
    lo.to_csv("results/selection_lowest.csv", index=False)
    hi.to_csv("results/selection_highest.csv", index=False)
    diff.to_csv("results/selection_diff.csv")

    max_rrg = diff.rrg.max()
    max_nlow = diff.n_low.max()
    max_nhigh = diff.n_high.max()
    max_cost = diff.federal_cost.max()
    max_part = diff.n_participating.max()

    print("Max absolute difference (lowest vs highest subsidy selection)")
    print(f"  RRG:                 {max_rrg:.6f}")
    print(f"  low-income moves:    {max_nlow:.0f}")
    print(f"  high-income moves:   {max_nhigh:.0f}")
    print(f"  federal cost ($):    {max_cost:,.0f}")
    print(f"  participating juris: {max_part:.0f}")

    identical = np.isclose(max_rrg, 0) and max_nlow == 0 and max_nhigh == 0 \
        and np.isclose(max_cost, 0) and max_part == 0
    print("\nRESULT:", "IDENTICAL equilibrium outcomes at every grid point"
          if identical else "DIFFERENCES FOUND - see results/selection_diff.csv")


if __name__ == "__main__":
    main()
