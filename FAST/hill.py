import os
import sys
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import t as t_dist
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Use Arial if available, otherwise fall back to the default sans-serif
if 'Arial' in [f.name for f in fm.fontManager.ttflist]:
    plt.rcParams['font.family'] = 'Arial'
else:
    plt.rcParams['font.family'] = 'sans-serif'


def hill_func(pCa, Smin, Smax, Ca50, n):
    Ca = 10.0 ** (-pCa)
    return Smin + (Smax - Smin) * Ca**n / (Ca50**n + Ca**n)


def run_hill_fit(data_file, speed_col='speed', pca_col='pCa', baseline_subtract=False):
    parent_dir  = os.path.dirname(os.path.abspath(data_file))
    folder_name = os.path.basename(parent_dir)
    csv_stem    = os.path.splitext(os.path.basename(data_file))[0]
    out_prefix  = os.path.join(parent_dir, folder_name + '_' + csv_stem)

    ext = os.path.splitext(data_file)[1].lower()
    if ext in ('.xlsx', '.xls'):
        df = pd.read_excel(data_file)
    elif ext == '.csv':
        df = pd.read_csv(data_file)
    else:
        sys.exit(f"Unsupported file format '{ext}'. Use .csv, .xls, or .xlsx")

    # Case-insensitive column matching
    col_map  = {c.strip().lower(): c for c in df.columns}
    pca_key  = pca_col.strip().lower()
    spd_key  = speed_col.strip().lower()
    if pca_key not in col_map:
        sys.exit(f"pCa column '{pca_col}' not found. Use -p to specify the column name.")
    if spd_key not in col_map:
        available = [c for c in df.columns if any(k in c.lower() for k in ('vel','speed','spd'))]
        hint = f"  Available velocity columns: {available}" if available else ""
        sys.exit(f"Speed column '{speed_col}' not found.{hint}\nUse -c to specify the column name.")

    df = df[[col_map[pca_key], col_map[spd_key]]].copy()
    df.columns = ['pca', 'speed']
    df = df.dropna()
    df['pca']   = df['pca'].astype(float)
    df['speed'] = df['speed'].astype(float)

    # Average any duplicate pCa values
    grouped    = df.groupby('pca')['speed'].mean().sort_index()
    pCa_data   = grouped.index.values
    speed_data = grouped.values

    # Optionally subtract pCa 9 baseline so that no-calcium speed = 0
    if baseline_subtract:
        pca9_mask = np.isclose(pCa_data, 9.0)
        if pca9_mask.any():
            speed_data = speed_data - speed_data[pca9_mask][0]
        else:
            print("Warning: no pCa 9 data found — baseline subtraction skipped")

    if len(pCa_data) < 4:
        sys.exit("At least 4 distinct pCa values are required for the 4-parameter fit")

    # Initial guesses and bounds
    Smin0  = 0.0
    Smax0  = float(speed_data.max())
    Ca50_0 = 10.0 ** (-float(np.median(pCa_data)))
    n0     = 2.0

    try:
        popt, pcov = curve_fit(
            hill_func, pCa_data, speed_data,
            p0=[Smin0, Smax0, Ca50_0, n0],
            bounds=([-Smax0 * 0.2, Smax0 * 0.5, 1e-10, 0.1],
                    [ Smax0 * 0.2, Smax0 * 3,  1e-3,  20.0]),
            maxfev=50000
        )
    except RuntimeError as e:
        sys.exit(f"Curve fitting failed: {e}")

    Smin_fit, Smax_fit, Ca50_fit, n_fit = popt
    pCa50_fit   = -np.log10(Ca50_fit)
    perr        = np.sqrt(np.diag(pcov))
    # 95% CI: t-critical for n_data - 4 degrees of freedom (4 parameters)
    t_crit      = t_dist.ppf(0.975, df=max(len(pCa_data) - 4, 1))
    ci          = t_crit * perr
    # pCa50 CI via error propagation: d(pCa50)/d(Ca50) = -1/(Ca50 * ln10)
    pCa50_ci    = t_crit * perr[2] / (Ca50_fit * np.log(10))
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
        f.write("Fitted Parameters (95% confidence interval)\n")
        f.write(f"  Smin             = {Smin_fit:10.4f} +/- {ci[0]:.4f} nm/s\n")
        f.write(f"  Smax             = {Smax_fit:10.4f} +/- {ci[1]:.4f} nm/s\n")
        f.write(f"  Ca50             = {Ca50_fit:10.4e} +/- {ci[2]:.4e} M\n")
        f.write(f"  pCa50            = {pCa50_fit:10.4f} +/- {pCa50_ci:.4f}\n")
        f.write(f"  n (Hill coeff.)  = {n_fit:10.4f} +/- {ci[3]:.4f}\n\n")
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
    ax.invert_xaxis()
    ax.set_xlabel('pCa')
    ax.set_ylabel('Speed (nm/s)')
    ax.set_title(folder_name + '_' + csv_stem)
    ax.legend(fontsize=8)
    plt.tight_layout()

    for ext in ('.pdf', '.png'):
        path = out_prefix + ext
        plt.savefig(path, dpi=150)
        print(f"Plot saved to:       {path}")
    plt.close()
