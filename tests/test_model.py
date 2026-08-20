"""Property-based checks tying the code to Propositions S1-S3.

Run with:  python -m pytest tests/  (or simply  python tests/test_model.py)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

import config as C
import population
import model


def test_required_subsidy_increasing_in_r():
    """Corollary S1: S_req is increasing in the discount rate."""
    pop = population.build_population().head(2000).copy()
    pop["r"] = C.R_LOW
    s_low = model.required_subsidy(pop)
    pop["r"] = C.R_HIGH
    s_high = model.required_subsidy(pop)
    assert np.all(s_high >= s_low)


def test_relocation_monotone_in_subsidy():
    """Prop. S1 comparative static: higher subsidy weakly raises relocation."""
    pop = population.build_population()
    s_req = model.required_subsidy(pop)
    n_prev = -1
    for s in [0, 50e3, 100e3, 150e3, 200e3, 250e3]:
        n = int((s_req <= s).sum())
        assert n >= n_prev
        n_prev = n


def test_participation_monotone_in_alpha():
    """Prop. S3: the participation set is monotone (an interval) in alpha."""
    pop = population.build_population()
    prev = None
    for a in np.arange(0.50, 1.001, 0.05):
        o = model.evaluate_policy(pop, float(a))
        if prev is not None:
            assert o.n_participating >= prev
        prev = o.n_participating


def test_seeded_reproducibility():
    p1 = population.build_population()
    p2 = population.build_population()
    assert np.allclose(p1["V"].values, p2["V"].values)
    assert len(p1) == 34493


if __name__ == "__main__":
    for fn in [test_required_subsidy_increasing_in_r,
               test_relocation_monotone_in_subsidy,
               test_participation_monotone_in_alpha,
               test_seeded_reproducibility]:
        fn()
        print(f"{fn.__name__}: OK")
