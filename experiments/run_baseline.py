"""Baseline alpha sweep (Figures 1-2 of the paper).

Writes results/baseline_sweep.csv and prints the minimal uniform federal
cost share required to reach each RRG benchmark (0.70 / 0.80 / 0.90).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config as C
import population
import model


def main():
    pop = population.build_population()
    df = model.sweep_alpha(pop)
    os.makedirs("results", exist_ok=True)
    df.to_csv("results/baseline_sweep.csv", index=False)

    print(df.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))
    print()
    for bench in C.RRG_BENCHMARKS:
        hit = df[df.rrg >= bench]
        if len(hit):
            a = hit.alpha.iloc[0]
            cost = hit.federal_cost.iloc[0]
            print(f"RRG >= {bench:.2f}: first reached at alpha = {a:.2f} "
                  f"(RRG = {hit.rrg.iloc[0]:.3f}, federal cost = ${cost/1e6:,.0f}M)")
        else:
            print(f"RRG >= {bench:.2f}: not reached on the alpha grid")

    at75 = df[df.alpha == 0.75].iloc[0]
    print(f"\nCurrent FEMA policy (alpha=0.75): RRG = {at75.rrg:.3f}, "
          f"low-income {at75.n_low}/{(pop.low_income).sum()} "
          f"({at75.low_rate*100:.2f}%), high-income {at75.n_high}/"
          f"{(~pop.low_income).sum()} ({at75.high_rate*100:.2f}%), "
          f"federal cost ${at75.federal_cost/1e6:,.0f}M")


if __name__ == "__main__":
    main()
