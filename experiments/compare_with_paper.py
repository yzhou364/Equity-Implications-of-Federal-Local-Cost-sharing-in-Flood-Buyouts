"""Side-by-side comparison of simulation output with the values reported
in the manuscript. Run after run_baseline.py and run_policies.py."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd

PAPER = [
    # (quantity, paper value)
    ("RRG at alpha=0.75",              0.26),
    ("low-income rate at 0.75 (%)",    1.1),
    ("high-income rate at 0.75 (%)",   4.0),
    ("federal cost at 0.75 ($M)",      82),
    ("RRG at alpha=0.85",              0.70),
    ("federal cost at 0.85 ($M)",      375),
    ("RRG at alpha=0.90",              0.87),
    ("federal cost at 0.90 ($M)",      648),
    ("RRG at alpha=1.00",              0.93),
    ("federal cost at 1.00 ($M)",      824),
]


def main():
    df = pd.read_csv("results/baseline_sweep.csv").set_index("alpha")
    sim = {
        "RRG at alpha=0.75": df.loc[0.75, "rrg"],
        "low-income rate at 0.75 (%)": df.loc[0.75, "low_rate"] * 100,
        "high-income rate at 0.75 (%)": df.loc[0.75, "high_rate"] * 100,
        "federal cost at 0.75 ($M)": df.loc[0.75, "federal_cost"] / 1e6,
        "RRG at alpha=0.85": df.loc[0.85, "rrg"],
        "federal cost at 0.85 ($M)": df.loc[0.85, "federal_cost"] / 1e6,
        "RRG at alpha=0.90": df.loc[0.90, "rrg"],
        "federal cost at 0.90 ($M)": df.loc[0.90, "federal_cost"] / 1e6,
        "RRG at alpha=1.00": df.loc[1.00, "rrg"],
        "federal cost at 1.00 ($M)": df.loc[1.00, "federal_cost"] / 1e6,
    }
    rows = [(q, p, sim[q]) for q, p in PAPER]
    out = pd.DataFrame(rows, columns=["quantity", "paper", "simulation"])
    out["simulation"] = out.simulation.round(2)
    out.to_csv("results/comparison_with_paper.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
