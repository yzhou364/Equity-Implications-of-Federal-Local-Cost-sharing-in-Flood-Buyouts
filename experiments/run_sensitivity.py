"""Sensitivity analyses (Results: Sensitivity Analysis).

1. Discount-rate heterogeneity: (r_high, r_low) in {(14,12), (18,12), (25,8)}%
   -> minimal alpha achieving RRG >= 0.70.
2. Subsidy cap: $250k vs $400k -> RRG at alpha = 0.75 and 0.90.
3. Climate scenarios: RRG at alpha = 0.75 under each RCP.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd

import config as C
import population
import model


def alpha_star(pop, bench=0.70, **kw):
    df = model.sweep_alpha(pop, **kw)
    hit = df[df.rrg >= bench]
    return (hit.alpha.iloc[0], hit.rrg.iloc[0]) if len(hit) else (None, None)


def main():
    os.makedirs("results", exist_ok=True)
    rows = []

    # --- discount-rate heterogeneity -------------------------------------
    for r_hi, r_lo in [(0.14, 0.12), (0.18, 0.12), (0.25, 0.08)]:
        C.R_HIGH, C.R_LOW = r_hi, r_lo
        pop = population.build_population()
        a, rrg = alpha_star(pop)
        rows.append(("discount", f"r_high={r_hi:.0%}, r_low={r_lo:.0%}",
                     f"alpha*(RRG>=0.70) = {a}", rrg))
        print(rows[-1])
    C.R_HIGH, C.R_LOW = 0.18, 0.12  # restore baseline

    # --- subsidy cap ------------------------------------------------------
    pop = population.build_population()
    for cap in [C.SUBSIDY_CAP, C.SUBSIDY_CAP_HIGH]:
        o75 = model.evaluate_policy(pop, 0.75, cap=cap)
        o90 = model.evaluate_policy(pop, 0.90, cap=cap)
        rows.append(("cap", f"S-bar=${cap/1e3:.0f}k",
                     f"RRG(0.75)={o75.rrg:.3f}, RRG(0.90)={o90.rrg:.3f}", None))
        print(rows[-1])

    # --- climate scenarios --------------------------------------------------
    for sc in list(C.CLIMATE) + [None]:
        o = model.evaluate_policy(pop, 0.75, scenario=sc)
        rows.append(("climate", sc or "expectation",
                     f"RRG(0.75)={o.rrg:.3f}", o.rrg))
        print(rows[-1])

    pd.DataFrame(rows, columns=["family", "case", "result", "value"]) \
        .to_csv("results/sensitivity.csv", index=False)


if __name__ == "__main__":
    main()
