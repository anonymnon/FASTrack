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


def _short_label(stem):
    '''
    Truncate a filename stem to the text before its first underscore, e.g.
    "WT_pCa_speed_extraSlides" -> "WT" - used for both the legend and the
    output filenames so a descriptive input name doesn't clutter either.
    '''
    return stem.split('_')[0]


def _normalize_curve(speed_data, data_file):
    '''
    Min-max scale speed_data to [0, 1] using this curve's own min/max (not
    shared across curves), so e.g. a 500 nm/s max and a 1000 nm/s max both
    become 1.0 on their own curve.
    '''
    lo, hi = speed_data.min(), speed_data.max()
    if hi == lo:
        sys.exit(f"Cannot normalize {data_file}: all speed values are identical (no range to normalize)")
    return (speed_data - lo) / (hi - lo)


def _load_pca_speed(data_file, speed_col, pca_col, baseline_subtract):
    '''
    Read data_file, pick out the pCa/speed columns (case-insensitive), average
    any duplicate pCa values, and optionally subtract the pCa 9 baseline.
    Returns (pCa_data, speed_data) as sorted-by-pCa numpy arrays.
    '''
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
        sys.exit(f"pCa column '{pca_col}' not found in {data_file}. Use -p to specify the column name.")
    if spd_key not in col_map:
        available = [c for c in df.columns if any(k in c.lower() for k in ('vel','speed','spd'))]
        hint = f"  Available velocity columns: {available}" if available else ""
        sys.exit(f"Speed column '{speed_col}' not found in {data_file}.{hint}\nUse -c to specify the column name.")

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
            print(f"Warning: no pCa 9 data found in {data_file} — baseline subtraction skipped")

    if len(pCa_data) < 4:
        sys.exit(f"At least 4 distinct pCa values are required for the 4-parameter fit ({data_file})")

    return pCa_data, speed_data


def _fit_hill(pCa_data, speed_data):
    '''
    Fit the 4-parameter Hill equation to pCa_data/speed_data and return a dict
    of everything needed to report and plot the result, including the speed
    at pCa50 (the midpoint of the fitted curve, i.e. (Smin+Smax)/2 - this is
    exact regardless of Ca50/n, since at Ca=Ca50 the Hill term is always 1/2)
    and its 95% confidence interval where computable.
    '''
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

    # Speed at pCa50 = (Smin+Smax)/2 exactly (the Hill term is 1/2 at Ca=Ca50
    # regardless of Ca50/n), with its CI via error propagation through
    # Smin/Smax and their covariance
    speed_at_pCa50    = (Smin_fit + Smax_fit) / 2.0
    var_speed_pCa50   = 0.25 * (pcov[0, 0] + pcov[1, 1] + 2 * pcov[0, 1])
    if np.isfinite(var_speed_pCa50) and var_speed_pCa50 >= 0:
        speed_at_pCa50_ci = t_crit * np.sqrt(var_speed_pCa50)
    else:
        speed_at_pCa50_ci = None

    return {
        'popt': popt, 'pcov': pcov, 'ci': ci, 't_crit': t_crit,
        'Smin_fit': Smin_fit, 'Smax_fit': Smax_fit, 'Ca50_fit': Ca50_fit, 'n_fit': n_fit,
        'pCa50_fit': pCa50_fit, 'pCa50_ci': pCa50_ci,
        'r_squared': r_squared, 'rmse': rmse, 'speed_pred': speed_pred,
        'speed_at_pCa50': speed_at_pCa50, 'speed_at_pCa50_ci': speed_at_pCa50_ci,
    }


def _format_fit_block(label, pCa_data, speed_data, fit, normalized=False):
    '''
    Render one file's fit results (parameters, goodness of fit, data table)
    as text, in the same format used by the single-file report. When
    normalized is True, the fit was run on 0-1 min-max-scaled speed data (see
    _normalize_curve), so speed-valued quantities are reported unitless
    instead of in nm/s.
    '''
    su = '' if normalized else ' nm/s'
    speed_header  = 'Speed (0-1)'  if normalized else 'Speed (nm/s)'
    fitted_header = 'Fitted (0-1)' if normalized else 'Fitted (nm/s)'

    lines = []
    lines.append(f"Hill Fit Results: {label}" + (" (normalized 0-1)" if normalized else ""))
    lines.append("=" * 60)
    lines.append("")
    lines.append("Fitted Parameters (95% confidence interval)")
    lines.append(f"  Smin             = {fit['Smin_fit']:10.4f} +/- {fit['ci'][0]:.4f}{su}")
    lines.append(f"  Smax             = {fit['Smax_fit']:10.4f} +/- {fit['ci'][1]:.4f}{su}")
    lines.append(f"  Ca50             = {fit['Ca50_fit']:10.4e} +/- {fit['ci'][2]:.4e} M")
    lines.append(f"  pCa50            = {fit['pCa50_fit']:10.4f} +/- {fit['pCa50_ci']:.4f}")
    lines.append(f"  n (Hill coeff.)  = {fit['n_fit']:10.4f} +/- {fit['ci'][3]:.4f}")
    if fit['speed_at_pCa50_ci'] is not None:
        lines.append(f"  Speed at pCa50   = {fit['speed_at_pCa50']:10.4f} +/- {fit['speed_at_pCa50_ci']:.4f}{su}")
    else:
        lines.append(f"  Speed at pCa50   = {fit['speed_at_pCa50']:10.4f}{su} (95% CI not available)")
    lines.append("")
    lines.append("Goodness of Fit")
    lines.append(f"  R²   = {fit['r_squared']:.6f}")
    lines.append(f"  RMSE = {fit['rmse']:.4f}{su}")
    lines.append("")
    lines.append("Data Points (pCa averaged)")
    lines.append(f"  {'pCa':>8}  {speed_header:>20}  {fitted_header:>20}")
    lines.append(f"  {'-' * 8}  {'-' * 20}  {'-' * 20}")
    for p, s, sf in zip(pCa_data, speed_data, fit['speed_pred']):
        lines.append(f"  {p:8.4f}  {s:20.4f}  {sf:20.4f}")
    return "\n".join(lines) + "\n"


def _fit_label(fit, prefix, normalized=False):
    '''
    Legend label for a fit line - the truncated filename label (see
    _short_label) followed by the pCa50/n/R²/max-speed/speed-at-pCa50
    summary. Data-point markers are plotted without a label (see callers) so
    they never show up in the legend.
    '''
    su = '' if normalized else ' nm/s'
    return (f'{prefix}: pCa50={fit["pCa50_fit"]:.2f}  n={fit["n_fit"]:.2f}  '
            f'R²={fit["r_squared"]:.4f}  Smax={fit["Smax_fit"]:.2f}{su}  '
            f'S(pCa50)={fit["speed_at_pCa50"]:.2f}{su}')


def run_hill_fit(data_file, speed_col='speed', pca_col='pCa', baseline_subtract=False, normalize=False):
    parent_dir  = os.path.dirname(os.path.abspath(data_file))
    csv_stem    = os.path.splitext(os.path.basename(data_file))[0]
    short_label = _short_label(csv_stem)
    suffix      = '_nl' if normalize else ''
    out_prefix  = os.path.join(parent_dir, short_label + suffix)

    # Normalization already zeroes the baseline (every curve's own minimum
    # becomes 0), so baseline subtraction would be redundant
    if normalize:
        baseline_subtract = False

    pCa_data, speed_data = _load_pca_speed(data_file, speed_col, pca_col, baseline_subtract)
    if normalize:
        speed_data = _normalize_curve(speed_data, data_file)
    fit = _fit_hill(pCa_data, speed_data)

    # ── Text output ────────────────────────────────────────────────────────────
    txt_file = out_prefix + '.txt'
    with open(txt_file, 'w') as f:
        f.write(_format_fit_block(os.path.basename(data_file), pCa_data, speed_data, fit, normalized=normalize))
    print(f"Results written to:  {txt_file}")

    # ── Plot ───────────────────────────────────────────────────────────────────
    pCa_smooth   = np.linspace(pCa_data.min(), pCa_data.max(), 500)
    speed_smooth = hill_func(pCa_smooth, *fit['popt'])

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(pCa_data, speed_data, 'o', color='black', markersize=6)
    ax.plot(pCa_smooth, speed_smooth, '-', color='red', linewidth=2,
            label=_fit_label(fit, prefix=short_label, normalized=normalize))
    ax.invert_xaxis()
    ax.set_xlabel('pCa')
    ax.set_ylabel('Normalized speed (0-1)' if normalize else 'Speed (nm/s)')
    ax.set_title(short_label + suffix)
    # Legend placed below the axes so it never narrows the plot area itself;
    # bbox_inches='tight' on savefig below expands the saved image's height
    # to include it rather than clipping it off
    ax.legend(fontsize=8, loc='upper center', bbox_to_anchor=(0.5, -0.15), borderaxespad=0)
    plt.tight_layout()

    for ext in ('.pdf', '.png'):
        path = out_prefix + ext
        plt.savefig(path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to:       {path}")
    plt.close()


def run_hill_fit_compare(data_file1, data_file2, speed_col='speed', pca_col='pCa',
                          speed_col2=None, pca_col2=None, baseline_subtract=False,
                          color1='black', color2='red', normalize=False):
    '''
    Fit two pCa/speed data files independently and plot both fits on the same
    graph (data_file1 in color1, data_file2 in color2 - default black/red),
    writing a single text file with the same results block as the single-file
    report for each of the two files. When normalize is True, each file is
    min-max scaled to its own [0, 1] range (see _normalize_curve) before
    fitting, independently of the other file's range.
    '''
    speed_col2 = speed_col2 or speed_col
    pca_col2   = pca_col2 or pca_col

    parent_dir1 = os.path.dirname(os.path.abspath(data_file1))
    stem1       = os.path.splitext(os.path.basename(data_file1))[0]
    stem2       = os.path.splitext(os.path.basename(data_file2))[0]
    short1      = _short_label(stem1)
    short2      = _short_label(stem2)
    suffix      = '_nl' if normalize else ''
    out_prefix  = os.path.join(parent_dir1, short1 + '_' + short2 + suffix)

    # Normalization already zeroes the baseline (every curve's own minimum
    # becomes 0), so baseline subtraction would be redundant
    if normalize:
        baseline_subtract = False

    pCa1, speed1 = _load_pca_speed(data_file1, speed_col, pca_col, baseline_subtract)
    pCa2, speed2 = _load_pca_speed(data_file2, speed_col2, pca_col2, baseline_subtract)

    if normalize:
        speed1 = _normalize_curve(speed1, data_file1)
        speed2 = _normalize_curve(speed2, data_file2)

    fit1 = _fit_hill(pCa1, speed1)
    fit2 = _fit_hill(pCa2, speed2)

    # ── Text output ────────────────────────────────────────────────────────────
    txt_file = out_prefix + '.txt'
    with open(txt_file, 'w') as f:
        f.write(_format_fit_block(os.path.basename(data_file1), pCa1, speed1, fit1, normalized=normalize))
        f.write("\n\n")
        f.write(_format_fit_block(os.path.basename(data_file2), pCa2, speed2, fit2, normalized=normalize))
    print(f"Results written to:  {txt_file}")

    # ── Plot ───────────────────────────────────────────────────────────────────
    pCa_smooth = np.linspace(min(pCa1.min(), pCa2.min()), max(pCa1.max(), pCa2.max()), 500)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(pCa1, speed1, 'o', color=color1, markersize=6)
    ax.plot(pCa_smooth, hill_func(pCa_smooth, *fit1['popt']), '-', color=color1, linewidth=2,
            label=_fit_label(fit1, prefix=short1, normalized=normalize))
    ax.plot(pCa2, speed2, 'o', color=color2, markersize=6)
    ax.plot(pCa_smooth, hill_func(pCa_smooth, *fit2['popt']), '-', color=color2, linewidth=2,
            label=_fit_label(fit2, prefix=short2, normalized=normalize))
    ax.invert_xaxis()
    ax.set_xlabel('pCa')
    ax.set_ylabel('Normalized speed (0-1)' if normalize else 'Speed (nm/s)')
    ax.set_title(short1 + '_' + short2 + suffix)
    # Legend placed below the axes so it never narrows the plot area itself;
    # bbox_inches='tight' on savefig below expands the saved image's height
    # to include it rather than clipping it off
    ax.legend(fontsize=8, loc='upper center', bbox_to_anchor=(0.5, -0.15), borderaxespad=0)
    plt.tight_layout()

    for ext in ('.pdf', '.png'):
        path = out_prefix + ext
        plt.savefig(path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to:       {path}")
    plt.close()
