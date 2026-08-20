"""Three-level stochastic Stackelberg game solver.

Implements the exact backward-induction algorithm of Supplementary
Materials Section S4:

  Stage 3 (households):  threshold rule, Prop. S1 / Corollary S1 (Eq. S5-S6)
  Stage 2 (local govts): finite candidate-set minimization, Prop. S2 (Eq. S7)
                         and participation test, Prop. S3 (Eq. S8)
  Stage 1 (federal):     grid evaluation of (alpha, S-bar)

No smoothing is applied at the household or local stages.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

import config as C


# ---------------------------------------------------------------------------
# Climate / damage paths
# ---------------------------------------------------------------------------

def slr_path(years: np.ndarray, scenario: str | None = None) -> np.ndarray:
    """Sea-level rise (m) at each year offset; scenario=None -> expectation."""
    frac = (C.BASE_YEAR + years - C.BASE_YEAR) / (C.END_YEAR - C.BASE_YEAR)
    if scenario is None:
        slr2100 = sum(v["p"] * v["slr2100"] for v in C.CLIMATE.values())
    else:
        slr2100 = C.CLIMATE[scenario]["slr2100"]
    return slr2100 * frac


def damage_growth(years: np.ndarray, scenario: str | None = None) -> np.ndarray:
    """Multiplicative damage growth factor 1 + beta * SLR(t)."""
    return 1.0 + C.BETA_SLR * slr_path(years, scenario)


# ---------------------------------------------------------------------------
# Stage 3: household thresholds (Prop. S1, Corollary S1)
# ---------------------------------------------------------------------------

def required_subsidy(pop: pd.DataFrame, scenario: str | None = None) -> np.ndarray:
    """Minimal subsidy inducing relocation within the program window (Eq. S6).

    S_req = C_rel - ((1+r)/r) * EAD(K_prog)
    """
    growth_k = damage_growth(np.array([C.PROGRAM_WINDOW]), scenario)[0]
    ead_k = pop["V"].values * pop["d"].values * growth_k
    c_rel = C.C_FIX + C.C_PROP * pop["V"].values
    return c_rel - (1.0 + pop["r"].values) / pop["r"].values * ead_k


def pv_expected_damages(pop: pd.DataFrame, scenario: str | None = None) -> np.ndarray:
    """Present value (at GOV_DISCOUNT) of expected damages over the horizon."""
    t = np.arange(C.HORIZON + 1)
    disc = (1.0 + C.GOV_DISCOUNT) ** (-t)
    factor = float(np.sum(disc * damage_growth(t, scenario)))
    return pop["V"].values * pop["d"].values * factor


# ---------------------------------------------------------------------------
# Stage 2: local best responses (Prop. S2) and participation (Prop. S3)
# ---------------------------------------------------------------------------

@dataclass
class JurisdictionOutcome:
    name: str
    participates: bool
    subsidy: float
    relocated: np.ndarray          # boolean mask over the jurisdiction's rows
    local_cost: float
    federal_cost: float
    n_tied_optima: int = 1


def solve_jurisdiction(sub: pd.DataFrame, s_req: np.ndarray, pv_dmg: np.ndarray,
                       alpha: float, cap: float,
                       selection: str = "lowest",
                       msr_rho: float | None = None) -> JurisdictionOutcome:
    """Exact minimization of Eq. (S2) over the candidate set of Eq. (S7)."""
    n = len(sub)
    mhi = sub["mhi_juris"].iloc[0]
    f_j = C.ADMIN_FIXED_BASE * n * (C.MHI_NATIONAL / mhi) ** C.CAPACITY_EXP

    # PV of the tax stream lost per acquisition
    t = np.arange(C.HORIZON + 1)
    tax_annuity = float(np.sum((1.0 + C.GOV_DISCOUNT) ** (-t))) * C.PROPERTY_TAX
    tax_loss_h = tax_annuity * sub["V"].values

    order = np.argsort(s_req)
    sr_sorted = s_req[order]
    pv_sorted = pv_dmg[order]
    tax_sorted = tax_loss_h[order]
    low_sorted = sub["low_income"].values[order]

    # Candidate subsidies: {0, S-bar} union feasible household thresholds
    cands = np.unique(np.concatenate([[0.0, cap],
                                      np.clip(sr_sorted, 0.0, None)]))
    cands = cands[cands <= cap]

    cum_pv = np.concatenate([[0.0], np.cumsum(pv_sorted)])
    cum_tax = np.concatenate([[0.0], np.cumsum(tax_sorted)])
    cum_low = np.concatenate([[0], np.cumsum(low_sorted)])
    total_pv = cum_pv[-1]
    n_low_total = int(low_sorted.sum())
    n_high_total = n - n_low_total

    # N(S): households with S_req <= S (right-continuous step function)
    ns = np.searchsorted(sr_sorted, cands, side="right")

    subsidy_cost = (1.0 - alpha) * cands * ns
    admin_cost = f_j + C.ADMIN_PER_ACQ * ns
    disaster_cost = C.SIGMA_LOC * (total_pv - cum_pv[ns])
    tax_cost = C.LAMBDA_TAX * cum_tax[ns]
    costs = subsidy_cost + admin_cost + disaster_cost + tax_cost

    # Minimum-service requirement: jurisdiction must achieve RRG_j >= rho.
    if msr_rho is not None and n_low_total > 0 and n_high_total > 0:
        low_rate = cum_low[ns] / n_low_total
        high_rate = (ns - cum_low[ns]) / n_high_total
        ok = (high_rate <= 0) | (low_rate >= msr_rho * high_rate)
        costs = np.where(ok, costs, np.inf)

    cmin = costs.min()
    ties = np.isclose(costs, cmin, rtol=0, atol=1e-6)
    idx = np.where(ties)[0]
    pick = idx[0] if selection == "lowest" else idx[-1]
    s_star = float(cands[pick])

    c0 = C.SIGMA_LOC * total_pv  # non-participation cost (Eq. S8 test)
    participates = np.isfinite(cmin) and (cmin <= c0)

    relocated = np.zeros(n, dtype=bool)
    fed_cost = 0.0
    local_cost = c0
    if participates:
        relocated_sorted = sr_sorted <= s_star
        inv = np.empty(n, dtype=int)
        inv[order] = np.arange(n)
        relocated = relocated_sorted[inv]
        fed_cost = alpha * s_star * relocated.sum()
        local_cost = float(cmin)

    return JurisdictionOutcome(sub["jurisdiction"].iloc[0], bool(participates),
                               s_star if participates else 0.0, relocated,
                               local_cost, fed_cost, int(ties.sum()))


# ---------------------------------------------------------------------------
# Stage 1: evaluate a federal policy
# ---------------------------------------------------------------------------

@dataclass
class PolicyOutcome:
    alpha: float
    cap: float
    rrg: float
    low_rate: float
    high_rate: float
    n_low: int
    n_high: int
    federal_cost: float
    n_participating: int
    n_jurisdictions: int
    max_ties: int = 1
    detail: pd.DataFrame | None = field(default=None, repr=False)


def evaluate_policy(pop: pd.DataFrame, alpha, cap: float = C.SUBSIDY_CAP,
                    scenario: str | None = None, selection: str = "lowest",
                    delta_s_low: float = 0.0, msr_rho: float | None = None,
                    keep_detail: bool = False) -> PolicyOutcome:
    """Solve the full game for one federal policy.

    ``alpha`` may be a scalar (uniform cost share) or a mapping
    jurisdiction -> alpha_j (equity-weighted cost sharing).
    ``delta_s_low`` implements income-tiered supplemental subsidies: a
    federally funded top-up DS paid to low-income buyout participants.
    Local governments choose subsidies on the base schedule (their cost
    share applies to S_j only), so the tier expands low-income take-up
    without altering local best responses.
    """
    s_req = required_subsidy(pop, scenario)
    pv_dmg = pv_expected_damages(pop, scenario)

    relocated = np.zeros(len(pop), dtype=bool)
    fed_cost, n_part, max_ties = 0.0, 0, 1
    detail_rows = []
    for name, idxs in pop.groupby("jurisdiction").indices.items():
        sub = pop.iloc[idxs]
        a_j = alpha[name] if isinstance(alpha, dict) else float(alpha)
        out = solve_jurisdiction(sub, s_req[idxs], pv_dmg[idxs], a_j, cap,
                                 selection=selection, msr_rho=msr_rho)
        if delta_s_low and out.participates:
            # federally funded top-up: low-income households relocate if
            # S_j + DS reaches their required subsidy
            low_mask = pop["low_income"].values[idxs]
            extra = low_mask & ~out.relocated & \
                (s_req[idxs] <= out.subsidy + delta_s_low)
            out.relocated = out.relocated | extra
            out.federal_cost += delta_s_low * (low_mask & out.relocated).sum()
        relocated[idxs] = out.relocated
        fed_cost += out.federal_cost
        n_part += out.participates
        max_ties = max(max_ties, out.n_tied_optima)
        detail_rows.append((name, sub["region"].iloc[0], a_j, out.participates,
                            out.subsidy, int(out.relocated.sum()), len(sub)))

    low = pop["low_income"].values
    low_rate = relocated[low].mean()
    high_rate = relocated[~low].mean()
    rrg = low_rate / high_rate if high_rate > 0 else np.nan
    detail = pd.DataFrame(detail_rows, columns=[
        "jurisdiction", "region", "alpha_j", "participates", "subsidy",
        "relocated", "households"]) if keep_detail else None
    return PolicyOutcome(float(np.mean(list(alpha.values())) if isinstance(alpha, dict) else alpha),
                         cap, rrg, low_rate, high_rate,
                         int(relocated[low].sum()), int(relocated[~low].sum()),
                         fed_cost, n_part,
                         pop["jurisdiction"].nunique(), max_ties, detail)


def sweep_alpha(pop: pd.DataFrame, alphas=C.ALPHA_GRID, **kw) -> pd.DataFrame:
    rows = []
    for a in alphas:
        o = evaluate_policy(pop, a, **kw)
        rows.append({"alpha": a, "rrg": o.rrg, "low_rate": o.low_rate,
                     "high_rate": o.high_rate, "n_low": o.n_low,
                     "n_high": o.n_high, "federal_cost": o.federal_cost,
                     "n_participating": o.n_participating})
    return pd.DataFrame(rows)
