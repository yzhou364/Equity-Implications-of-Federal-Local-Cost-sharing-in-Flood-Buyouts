"""Regenerate Figures 1-4 of the paper from simulation output.

Run experiments/run_baseline.py and experiments/run_policies.py first
(or let this script run them automatically if the CSVs are missing).
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import config as C

BLUE, RED, DARK, LIGHT = "#1f4e8c", "#b03a2e", "#33415c", "#8fa7c9"


def _ensure(path, script):
    if not os.path.exists(path):
        os.system(f"python {script}")


def fig1():
    df = pd.read_csv("results/baseline_sweep.csv")
    fig, ax1 = plt.subplots(figsize=(7, 4.5))
    ax1.plot(df.alpha, df.rrg, color=BLUE, lw=2, label="RRG")
    ax1.axvline(0.75, color="grey", ls="--", lw=1)
    ax1.axhline(0.70, color=BLUE, ls=":", lw=1)
    ax1.set_xlabel("Federal cost-share ratio α")
    ax1.set_ylabel("Relocation ratio gap (RRG)", color=BLUE)
    ax1.set_ylim(0, 1)
    ax2 = ax1.twinx()
    ax2.plot(df.alpha, df.federal_cost / 1e6, color=RED, lw=2, label="Federal cost")
    ax2.set_ylabel("Federal cost ($ million)", color=RED)
    fig.tight_layout()
    fig.savefig("figures/Figure1_equity_vs_alpha.png", dpi=300)


def fig2():
    df = pd.read_csv("results/baseline_sweep.csv")
    sel = df[df.alpha.round(2).isin([0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00])]
    x = range(len(sel))
    w = 0.38
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar([i - w / 2 for i in x], sel.n_low, w, color=DARK, label="Low-income")
    ax.bar([i + w / 2 for i in x], sel.n_high, w, color=LIGHT, label="High-income")
    ax.set_xticks(list(x), [f"{a:.2f}" for a in sel.alpha])
    ax.set_xlabel("Federal cost-share ratio α")
    ax.set_ylabel("Households relocated")
    ax.legend()
    fig.tight_layout()
    fig.savefig("figures/Figure2_relocation_by_income.png", dpi=300)


def fig3():
    names = list(C.REGIONS)
    vals = [C.REGIONS[n] for n in names]
    panels = [("Mean property value ($000)", [v[1] / 1e3 for v in vals]),
              ("Low-income share (%)", [v[2] * 100 for v in vals]),
              ("Flood exposure (%)", [v[3] * 100 for v in vals]),
              ("Mean elevation (m)", [v[4] for v in vals])]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, (title, y) in zip(axes.flat, panels):
        ax.bar(names, y, color=BLUE)
        ax.set_title(title, fontsize=10)
        ax.tick_params(axis="x", rotation=60, labelsize=8)
    fig.tight_layout()
    fig.savefig("figures/Figure3_regional_heterogeneity.png", dpi=300)


def fig4():
    df = pd.read_csv("results/policy_comparison.csv")
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    sc = ax.scatter(df.federal_cost / 1e6, df.rrg, s=80, color=BLUE)
    for _, r in df.iterrows():
        ax.annotate(r.policy, (r.federal_cost / 1e6, r.rrg), fontsize=8,
                    xytext=(6, 4), textcoords="offset points")
    ax.set_xlabel("Federal cost ($ million)")
    ax.set_ylabel("Relocation ratio gap (RRG)")
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig("figures/Figure4_policy_comparison.png", dpi=300)


if __name__ == "__main__":
    os.makedirs("figures", exist_ok=True)
    _ensure("results/baseline_sweep.csv", "experiments/run_baseline.py")
    _ensure("results/policy_comparison.csv", "experiments/run_policies.py")
    fig1(); fig2(); fig3(); fig4()
    print("Figures written to figures/")
