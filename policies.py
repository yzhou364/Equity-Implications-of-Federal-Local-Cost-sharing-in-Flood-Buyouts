"""Alternative policy mechanisms (Results: Alternative Policy Mechanisms).

* Equity-weighted cost sharing: alpha_j = EW_BASE + EW_GAMMA * (MHI_nat -
  MHI_j), with median household income measured in units of $10,000 and
  alpha_j clipped to [EW_MIN, EW_MAX]. A continuous generalization of
  FEMA's 90% provision for small impoverished communities.
* Income-tiered subsidies: supplemental federal subsidy DELTA_S to
  low-income households.
* Minimum service requirements: participating jurisdictions must achieve
  RRG_j >= rho within their boundaries.
"""

import pandas as pd

import config as C
import model

EW_BASE = 0.75   # anchored at the current statutory federal share
EW_GAMMA = 0.10
EW_MIN, EW_MAX = 0.70, 0.90  # ceiling matches BRIC's 90% small-impoverished-community provision
DELTA_S = 15_000  # tier that approximately equalizes relocation rates in this calibration
DELTA_S_PAPER = 75_000  # value quoted in the manuscript (original calibration)
MSR_RHO = 0.80


def equity_weighted_alphas(pop: pd.DataFrame, base=EW_BASE, gamma=EW_GAMMA):
    mhi = pop.groupby("jurisdiction")["mhi_juris"].first() / 10_000.0
    mhi_nat = C.MHI_NATIONAL / 10_000.0
    a = (base + gamma * (mhi_nat - mhi)).clip(EW_MIN, EW_MAX)
    return a.to_dict()


def run_all(pop: pd.DataFrame) -> pd.DataFrame:
    rows = []

    o = model.evaluate_policy(pop, 0.75)
    rows.append(("Current FEMA 75/25", 0.75, o.rrg, o.federal_cost,
                 o.n_low + o.n_high, o.n_participating))

    o = model.evaluate_policy(pop, 0.90)
    rows.append(("Uniform alpha=0.90", 0.90, o.rrg, o.federal_cost,
                 o.n_low + o.n_high, o.n_participating))

    alphas = equity_weighted_alphas(pop)
    o = model.evaluate_policy(pop, alphas)
    rows.append((f"Equity-weighted (gamma={EW_GAMMA})", sum(alphas.values()) / len(alphas),
                 o.rrg, o.federal_cost, o.n_low + o.n_high, o.n_participating))

    o = model.evaluate_policy(pop, 0.75, delta_s_low=DELTA_S)
    rows.append((f"Income-tiered (dS=${DELTA_S//1000}k)", 0.75, o.rrg,
                 o.federal_cost, o.n_low + o.n_high, o.n_participating))

    o = model.evaluate_policy(pop, 0.90, msr_rho=MSR_RHO)
    rows.append((f"Min service rho={MSR_RHO} (alpha=0.90)", 0.90, o.rrg,
                 o.federal_cost, o.n_low + o.n_high, o.n_participating))

    return pd.DataFrame(rows, columns=["policy", "mean_alpha", "rrg",
                                       "federal_cost", "relocations",
                                       "participating"])
