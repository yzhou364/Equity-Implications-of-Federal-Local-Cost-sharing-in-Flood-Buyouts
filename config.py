"""Model configuration and calibrated parameters.

All symbols follow the notation of the paper and its Supplementary
Materials (Eqs. S1-S8). Regional data reproduce Table 1 of the paper.
"""

import numpy as np

SEED = 20250501  # global random seed for the synthetic population

# ---------------------------------------------------------------------------
# Regional parameters (Table 1 of the paper)
# households, mean property value ($), low-income share, share in 100-yr
# floodplain, mean elevation (m), median household income ($, ACS-based)
# ---------------------------------------------------------------------------
REGIONS = {
    #  name             N     meanV     lowinc  exposure  elev   MHI
    "Brooklyn":        (5200,   650_000, 0.45,  0.35,     2.0,   70_000),
    "Staten Island":   (2800,   580_000, 0.52,  0.42,     1.8,   85_000),
    "Queens":          (4100,   520_000, 0.58,  0.65,     1.5,   75_000),
    "Lower Manhattan": (1850, 1_850_000, 0.15,  0.45,     2.0,  140_000),
    "Houston":         (6500,   285_000, 0.55,  0.38,     9.0,   60_000),
    "New Orleans":     (4200,   265_000, 0.62,  0.75,     0.5,   45_000),
    "Miami-Dade":      (5100,   485_000, 0.48,  0.52,     1.5,   60_000),
    "Charleston":      (2350,   425_000, 0.42,  0.55,     2.5,   65_000),
    "Norfolk":         (2393,   245_000, 0.50,  0.48,     1.5,   55_000),
}
MHI_NATIONAL = 75_000

# Each region is administered as two jurisdictions (a higher- and a
# lower-income service area), reflecting sub-county program administration.
JURISDICTIONS_PER_REGION = 2

# ---------------------------------------------------------------------------
# Climate scenarios: IPCC RCPs, sea-level rise by 2100 (m), probabilities
# ---------------------------------------------------------------------------
CLIMATE = {
    "RCP2.6": {"p": 0.2, "slr2100": 0.4},
    "RCP4.5": {"p": 0.5, "slr2100": 0.6},
    "RCP8.5": {"p": 0.3, "slr2100": 1.0},
}
BASE_YEAR = 2025
END_YEAR = 2100

# ---------------------------------------------------------------------------
# Household parameters
# ---------------------------------------------------------------------------
R_HIGH = 0.18          # effective discount rate, low-income households
R_LOW = 0.12           # effective discount rate, high-income households
HORIZON = 50           # decision horizon T (years)
PROGRAM_WINDOW = 10    # relocation counted if optimal year k* <= window
V_SIGMA = 0.35         # lognormal sigma of property values within region
LOWINC_VALUE_MULT = 0.80  # low-income households occupy cheaper homes

# Gross relocation cost: C_rel = C_FIX + C_PROP * V  (moving, transaction,
# and destination housing-cost differential)
C_FIX = 111_580
C_PROP = 0.3453

# ---------------------------------------------------------------------------
# Flood damage process
# EAD_h(t) = V_h * d_h * (1 + BETA_SLR * SLR(t)), Eq. (S1) damage path.
# d_h: baseline expected annual damage ratio, lognormal around the
# regional base rate d0_j = D0_GLOBAL * exp(-elev_j / ELEV_SCALE).
# ---------------------------------------------------------------------------
D0_GLOBAL = 0.02095  # baseline EAD ratio at sea level, in-floodplain
ELEV_SCALE = 6.0       # e-folding elevation for flood hazard (m)
D_SIGMA = 0.30  # lognormal dispersion of household hazard
D_OUT_FRACTION = 0.10  # out-of-floodplain hazard relative to in-floodplain
BETA_SLR = 0.89  # damage amplification per metre of sea-level rise

# ---------------------------------------------------------------------------
# Local government parameters (Eq. S2)
# ---------------------------------------------------------------------------
GOV_DISCOUNT = 0.03    # local/federal planning discount rate
SIGMA_LOC = 0.8936  # share of household flood losses borne locally
ADMIN_PER_ACQ = 22_360  # a_j: administrative cost per completed acquisition
ADMIN_FIXED_BASE = 1370.9  # F_j scale ($ per resident household, see model.py)
CAPACITY_EXP = 0.89  # F_j ~ (MHI_nat / MHI_j)^CAPACITY_EXP
LAMBDA_TAX = 1.141  # lambda_j: tax-base preservation weight
PROPERTY_TAX = 0.012   # annual property tax rate

# ---------------------------------------------------------------------------
# Federal policy space
# ---------------------------------------------------------------------------
ALPHA_GRID = np.round(np.arange(0.50, 1.0001, 0.01), 2)
SUBSIDY_CAP = 250_000        # baseline maximum subsidy S-bar
SUBSIDY_CAP_HIGH = 400_000   # alternative cap (sensitivity analysis)

# Near-equity reporting benchmark used in the paper
RRG_BENCHMARKS = (0.70, 0.80, 0.90)
