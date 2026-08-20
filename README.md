# Equity Implications of Federal–Local Cost-Sharing in Flood Buyouts

Simulation code and data for:

> Zhou, Y. *Equity Implications of Federal–Local Cost-Sharing in Flood Buyouts:
> A Game-Theoretic Analysis with Heterogeneous Homeowners.*

The repository implements the three-level stochastic Stackelberg game described
in the paper's Methods and Supplementary Materials: a federal government sets
the cost-share ratio α and subsidy cap S̄; local governments simultaneously
choose participation and subsidy levels; heterogeneous households choose
relocation timing. The solver uses exact backward induction (no smoothing):
household threshold rules (Supplementary Eq. S5–S6), finite candidate-set
minimization for local governments (Eq. S7), the participation test (Eq. S8),
and grid evaluation of federal policy.

## Structure

```
config.py                          # all parameters; Table 1 regional data
population.py                      # synthetic household population (N = 34,493)
model.py                           # three-level game solver (Props. S1–S4)
policies.py                        # alternative policy mechanisms
calibrate.py                       # calibration of free parameters
figures.py                         # regenerate Figures 1–4
experiments/
  run_baseline.py                  # α sweep; RRG benchmarks (Figs. 1–2)
  run_policies.py                  # policy comparison (Fig. 4)
  run_sensitivity.py               # discount / cap / climate sensitivity
  run_selection_robustness.py      # equilibrium-selection check (SM §S3.5)
results/                           # CSV output (written by the scripts)
figures/                           # PNG output of figures.py
```

## Installation

```bash
pip install -r requirements.txt   # numpy, pandas, matplotlib
```

## Reproducing the paper's results

```bash
python experiments/run_baseline.py              # Figure 1–2, RRG benchmarks
python experiments/run_policies.py              # Figure 4 comparison
python experiments/run_sensitivity.py           # sensitivity analyses
python experiments/run_selection_robustness.py  # SM §S3.5 check
python figures.py                               # regenerate figures
```

Each run completes in seconds on a standard workstation. The synthetic
population is generated with a fixed random seed (`config.SEED`), so all
results are exactly reproducible.

## Notes

- Regional parameters (Table 1) are calibrated to FEMA National Flood Hazard
  Layer, US Census ACS, PropertyShark/Zillow, and USGS elevation data.
- Each region is administered as two jurisdictions (a higher- and a
  lower-income service area), giving 18 jurisdictions in total.
- Free parameters not pinned by data or literature were calibrated to the
  headline outcomes reported in the paper (see `calibrate.py` for the target
  set and procedure); `config.py` stores the calibrated values.
- The equity-weighted mechanism is implemented as
  α_j = ᾱ + γ·(MHI_nat − MHI_j) with MHI in units of $10,000 and α_j clipped
  to [0.70, 0.95] (see `policies.py`).

## License

MIT — see `LICENSE`.
