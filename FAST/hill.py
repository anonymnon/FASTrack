import os
import sys
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def hill_func(pCa, Vmax, pCa50, n):
    return Vmax / (1.0 + 10.0 ** (n * (pCa - pCa50)))


def run_hill_fit(data_file):
    parent_dir  = os.path.dirname(os.path.abspath(data_file))
    folder_name = os.path.basename(parent_dir)
    out_prefix  = os.path.join(parent_dir, folder_name)

    ext = os.path.splitext(data_file)[1].lower()
    if ext in ('.xlsx', '.xls'):
        df = pd.read_excel(data_file)
    elif ext == '.csv':
        df = pd.read_csv(data_file)
    else:
        sys.exit(f"Unsupported file format '{ext}'. Use .csv, .xls, or .xlsx")

    # Case-insensitive column matching
    col_map = {c.strip().lower(): c for c in df.columns}
    if 'pca' not in col_map or 'speed' not in col_map:
        sys.exit("File must contain columns named 'pCa' and 'speed' (case-insensitive)")
    df = df.rename(columns={col_map['pca']: 'pca', col_map['speed']: 'speed'})

    # Average duplicates
    grouped    = df.groupby('pca')['speed'].mean().reset_index().sort_values('pca')
    pCa_data   = grouped['pca'].values.astype(float)
    speed_data = grouped['speed'].values.astype(float)

    if len(pCa_data) < 3:
        sys.exit("At least 3 distinct pCa values are required for fitting")

    # Initial guesses
    Vmax0   = float(speed_data.max())
    pCa50_0 = float(pCa_data.mean())
    n0      = 2.0

    try:
        popt, pcov = curve_fit(
            hill_func, pCa_data, speed_data,
            p0=[Vmax0, pCa50_0, n0],
            bounds=([0, pCa_data.min() - 2, 0.1],
                    [Vmax0 * 5, pCa_data.max() + 2, 20]),
            maxfev=20000
        )
    except RuntimeError as e:
        sys.exit(f"Curve fitting failed: {e}")

    Vmax_fit, pCa50_fit, n_fit = popt
    perr        = np.sqrt(np.diag(pcov))
    speed_pred  = hill_func(pCa_data, *popt)
    ss_res      = np.sum((speed_data - speed_pred) ** 2)
    ss_tot      = np.sum((speed_data - np.mean(speed_data)) ** 2)
    r_squared   = 1.0 - ss_res / ss_tot if ss_tot > 0 else float('nan')
    rmse        = np.sqrt(np.mean((speed_data - speed_pred) ** 2))

    # ── Text output ────────────────────────────────────────────────────────────
    txt_file = out_prefix + '.txt'
    with open(txt_file, 'w') as f:
        f.write(f"Hill Fit Results: {os.path.basename(data_file)}\n")
        f.write("=" * 60 + "\n\n")
        f.write("Fitted Parameters\n")
        f.write(f"  Vmax             = {Vmax_fit:10.4f} +/- {perr[0]:.4f} nm/s\n")
        f.write(f"  pCa50            = {pCa50_fit:10.4f} +/- {perr[1]:.4f}\n")
        f.write(f"  n (Hill coeff.)  = {n_fit:10.4f} +/- {perr[2]:.4f}\n\n")
        f.write("Goodness of Fit\n")
        f.write(f"  R²   = {r_squared:.6f}\n")
        f.write(f"  RMSE = {rmse:.4f} nm/s\n\n")
        f.write("Data Points (pCa averaged)\n")
        f.write(f"  {'pCa':>8}  {'Speed (nm/s)':>14}  {'Fitted (nm/s)':>14}\n")
        f.write(f"  {'-' * 8}  {'-' * 14}  {'-' * 14}\n")
        for p, s, sf in zip(pCa_data, speed_data, speed_pred):
            f.write(f"  {p:8.4f}  {s:14.4f}  {sf:14.4f}\n")
    print(f"Results written to:  {txt_file}")

    # ── Plot ───────────────────────────────────────────────────────────────────
    pCa_smooth   = np.linspace(pCa_data.min(), pCa_data.max(), 500)
    speed_smooth = hill_func(pCa_smooth, *popt)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(pCa_data, speed_data, 'o', color='black', markersize=6,
            label='Data (mean per pCa)')
    ax.plot(pCa_smooth, speed_smooth, '-', color='red', linewidth=2,
            label=f'Hill fit  pCa50={pCa50_fit:.2f}  n={n_fit:.2f}  R²={r_squared:.4f}')
    ax.set_xlabel('pCa')
    ax.set_ylabel('Speed (nm/s)')
    ax.set_title(folder_name)
    ax.legend(fontsize=8)
    plt.tight_layout()

    for ext in ('.pdf', '.png'):
        path = out_prefix + ext
        plt.savefig(path, dpi=150)
        print(f"Plot saved to:       {path}")
    plt.close()
