"""Synthetic household population (Methods: Household Population).

Generates 34,493 households across nine regions, calibrated to the
observed distributions of property values, income mix, flood-zone
location, and elevation summarized in Table 1 of the paper.
"""

import numpy as np
import pandas as pd

import config as C


def build_population(seed: int = C.SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for name, (n, mean_v, low_share, exposure, elev, mhi) in C.REGIONS.items():
        low_income = rng.random(n) < low_share

        # Property values: truncated lognormal around the regional mean,
        # with low-income households occupying cheaper housing.
        mu = np.log(mean_v) - 0.5 * C.V_SIGMA**2
        v = rng.lognormal(mu, C.V_SIGMA, n)
        v = np.clip(v, 0.3 * mean_v, 4.0 * mean_v)
        v = np.where(low_income, v * C.LOWINC_VALUE_MULT, v)

        # Flood hazard: baseline expected annual damage ratio d_h.
        in_fp = rng.random(n) < exposure
        d0 = C.D0_GLOBAL * np.exp(-elev / C.ELEV_SCALE)
        z = rng.lognormal(0.0, C.D_SIGMA, n)
        d = d0 * z * np.where(in_fp, 1.0, C.D_OUT_FRACTION)

        # Discount rates by income group (Warner & Pleeter 2001; Bier et al. 2019)
        r = np.where(low_income, C.R_HIGH, C.R_LOW)

        # Two jurisdictions per region: households sorted into a lower- and a
        # higher-income service area (spatial income sorting).
        p_poorside = np.where(low_income, 0.75, 0.25)
        juris_poor = rng.random(n) < p_poorside

        rows.append(pd.DataFrame({
            "region": name,
            "jurisdiction": [f"{name}-{'B' if jp else 'A'}" for jp in juris_poor],
            "low_income": low_income,
            "V": v,
            "r": r,
            "d": d,
            "in_floodplain": in_fp,
            "mhi_region": mhi,
        }))
    df = pd.concat(rows, ignore_index=True)

    # Jurisdiction median household income: region MHI shifted by the
    # jurisdiction's realized income mix.
    juris_low = df.groupby("jurisdiction")["low_income"].mean()
    region_low = df.groupby("jurisdiction")["region"].first().map(
        {k: v[2] for k, v in C.REGIONS.items()})
    mhi_region = df.groupby("jurisdiction")["mhi_region"].first()
    juris_mhi = mhi_region * (1.0 - 0.55 * (juris_low - region_low))
    df["mhi_juris"] = df["jurisdiction"].map(juris_mhi)
    return df


if __name__ == "__main__":
    pop = build_population()
    print(pop.groupby("region").agg(N=("V", "size"), meanV=("V", "mean"),
                                    low=("low_income", "mean")))
    print(f"total households: {len(pop)}")
