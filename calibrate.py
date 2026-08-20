"""Calibration of free model parameters to the paper's reported outcomes.

Targets (main text, Figures 1 and 4):
  alpha=0.75: RRG=0.26, low-income rate=1.1%, high-income rate=4.0%, cost=$82M
  alpha=0.85: RRG=0.70, cost=$375M
  alpha=0.90: RRG=0.87, cost=$648M
  alpha=1.00: RRG=0.93, cost=$824M

Free parameters: those not pinned by data or the literature (hazard scale
and dispersion, relocation cost schedule, local cost weights, and the
administrative-capacity scaling of fixed program costs).
"""

import json
import sys

import numpy as np

import config as C
import population
import model

TARGETS = {
    0.75: {"rrg": 0.26, "cost": 82e6, "low_rate": 0.011, "high_rate": 0.040,
           "part": 8},
    0.85: {"rrg": 0.70, "cost": 375e6, "part": 10},
    0.90: {"rrg": 0.87, "cost": 648e6, "part": 12},
    1.00: {"rrg": 0.93, "cost": 824e6},
}

PARAM_SPACE = {  # name: (low, high, log?)
    "D0_GLOBAL":        (0.002, 0.030, True),
    "D_SIGMA":          (0.30, 1.20, False),
    "C_FIX":            (40e3, 130e3, False),
    "C_PROP":           (0.15, 0.45, False),
    "SIGMA_LOC":        (0.05, 1.20, True),
    "LAMBDA_TAX":       (0.10, 2.50, True),
    "ADMIN_FIXED_BASE": (50, 3000, True),
    "CAPACITY_EXP":     (0.3, 5.0, False),
    "LOWINC_VALUE_MULT": (0.50, 0.80, False),
    "ADMIN_PER_ACQ":    (5e3, 40e3, True),
    "BETA_SLR":         (0.8, 3.0, False),
}


def apply_params(params: dict):
    for k, v in params.items():
        setattr(C, k, v)


def loss_and_summary(params: dict):
    apply_params(params)
    pop = population.build_population()
    loss, summary = 0.0, {}
    for a, tg in TARGETS.items():
        o = model.evaluate_policy(pop, a)
        summary[a] = {"rrg": o.rrg, "cost": o.federal_cost,
                      "low_rate": o.low_rate, "high_rate": o.high_rate,
                      "part": o.n_participating}
        loss += 60.0 * (o.rrg - tg["rrg"]) ** 2
        loss += 3.0 * ((o.federal_cost - tg["cost"]) / tg["cost"]) ** 2
        if "low_rate" in tg:
            loss += 8.0 * ((o.low_rate - tg["low_rate"]) / tg["low_rate"]) ** 2
            loss += 8.0 * ((o.high_rate - tg["high_rate"]) / tg["high_rate"]) ** 2
        if "part" in tg:
            loss += 0.15 * (o.n_participating - tg["part"]) ** 2

    # Anchor: the paper's headline claim that near-equity (RRG >= 0.70)
    # first obtains at alpha = 0.85 on the 0.01 grid.
    a_star = None
    for a in np.round(np.arange(0.80, 0.951, 0.01), 2):
        if model.evaluate_policy(pop, a).rrg >= 0.70:
            a_star = a
            break
    summary["alpha_star_070"] = a_star
    loss += 300.0 * ((a_star if a_star is not None else 0.99) - 0.85) ** 2
    return loss, summary


def sample(rng):
    p = {}
    for k, (lo, hi, log) in PARAM_SPACE.items():
        u = rng.random()
        p[k] = float(np.exp(np.log(lo) + u * (np.log(hi) - np.log(lo)))) if log \
            else float(lo + u * (hi - lo))
    return p


def perturb(base, rng, scale=0.15):
    p = {}
    for k, (lo, hi, log) in PARAM_SPACE.items():
        v = base[k]
        if log:
            v = float(np.exp(np.log(v) + rng.normal(0, scale)))
        else:
            v = float(v + rng.normal(0, scale) * (hi - lo))
        p[k] = float(np.clip(v, lo, hi))
    return p


def main(n_random=250, n_refine=150, seed=7, warm_start=None):
    rng = np.random.default_rng(seed)
    best, best_loss, best_sum = None, np.inf, None
    if warm_start:
        with open(warm_start) as f:
            best = json.load(f)["params"]
        for k, (lo, hi, _) in PARAM_SPACE.items():
            best.setdefault(k, float(getattr(C, k)))
            best[k] = float(np.clip(best[k], lo, hi))
        best_loss, best_sum = loss_and_summary(best)
        print(f"[warm start] loss={best_loss:.3f}")
    for i in range(n_random):
        p = sample(rng)
        try:
            l, s = loss_and_summary(p)
        except Exception:
            continue
        if l < best_loss:
            best, best_loss, best_sum = p, l, s
            print(f"[random {i}] loss={l:.3f}")
    for i in range(n_refine):
        p = perturb(best, rng, scale=0.12 * (1 - i / n_refine) + 0.03)
        try:
            l, s = loss_and_summary(p)
        except Exception:
            continue
        if l < best_loss:
            best, best_loss, best_sum = p, l, s
            print(f"[refine {i}] loss={l:.3f}")
    print("\nBEST loss:", best_loss)
    print(json.dumps(best, indent=2))
    for a, s in best_sum.items():
        if a == "alpha_star_070":
            print(f"alpha*(RRG>=0.70) = {s}")
            continue
        print(f"alpha={a}: RRG={s['rrg']:.3f} cost=${s['cost']/1e6:.0f}M "
              f"low={s['low_rate']*100:.2f}% high={s['high_rate']*100:.2f}% part={s['part']}")
    with open("results/calibrated_params.json", "w") as f:
        json.dump({"loss": best_loss, "params": best}, f, indent=2)


if __name__ == "__main__":
    kw = {}
    if len(sys.argv) > 1:
        kw["n_random"] = int(sys.argv[1])
    if len(sys.argv) > 2:
        kw["n_refine"] = int(sys.argv[2])
    if len(sys.argv) > 3:
        kw["warm_start"] = sys.argv[3]
    main(**kw)
