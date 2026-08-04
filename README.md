# FAST v2.0.0: Fast Automated Spud Tracker

Please cite [**Aksel T, Yu EC, Sutton S, Ruppel KM, Spudich JA. Cell Reports. 2015. Ensemble force changes that result from human cardiac myosin mutations and a small molecule effector.**][1]

[1]: http://www.cell.com/cell-reports/abstract/S2211-1247(15)00381-2

**examples** folder containing all example movies can be downloaded from https://goo.gl/87LyDG

&copy; 2020 Tural Aksel

## Foreword

This fork started as a minor update to Tural Aksel's original FASTrack program to fix issues running it on modern Ubuntu, plus a new image-import script (**stack2tifs**, see below). Since then it has been substantially modernized using **Claude Code** (Anthropic's AI coding assistant) as a development tool. Changes made with Claude Code's help include:

- A full port of the codebase from Python 2 to Python 3 (the original program targeted Python 2 and required a Python 2/3 split toolchain).
- Replacement of the per-frame GNU-parallel subprocess pipeline with a persistent `multiprocessing` worker pool for faster, simpler parallel frame processing (GNU `parallel` is no longer a required dependency).
- Bug fixes in the filament link-scoring/disambiguation logic (`make_frame_links`, `wire_frame_links` in `FAST/motility.py`) that affected how confidently two filament detections in adjacent frames are linked into the same track.
- A typo fix so the `-dlascore` command-line option actually reaches the underlying analysis code (previously silently ignored).
- Various Python 3 compatibility fixes (integer division, deprecated `skimage`/`numpy` APIs, ragged `np.save`/`np.load` array handling, etc.).
- New movie-overlay rendering (raw frames blended onto the `paths_2D.png` tracking background, encoded as a cross-platform `.mp4` via `ffmpeg`) and pixel-exact frame sizing so tracking overlays line up with the raw `.tif` frames.
- Removal of the ImageJ-based contrast/threshold preprocessing step from `stack2tifs` (formerly `stack2tifspy3`) in favor of a pure-Python percentile contrast stretch. FAST's own entropy-island-based segmentation and per-filament skeletonization (in `FAST/motility.py`) already does a far better job of finding filaments when given properly contrast-stretched raw frames than the old ImageJ enhance-contrast/threshold/mask pipeline did - and dropping ImageJ also means FAST no longer needs a JVM, Java, or Maven installed at all.
- Auto-detection of the optimal frame bit depth in `stack2tifs`: a frame that already uses most of its native dtype's intensity range keeps that bit depth, otherwise it's quantized down to 8-bit while contrast-stretching, since the usable dynamic range doesn't need more than that to be represented losslessly.
- A `-sm`/`-sfps` option to generate a movie of just the skeletonized filaments (no trajectory arrows), with filaments belonging to a path classified as stuck rendered in red for every frame that path spans.
- `fast` now skips leaf directories with fewer than 2 frames instead of stalling on them, since a single frame can never produce a link, path, or velocity.
- Fixed a Windows packaging bug where `fast`/`lima`/`stack2tifs` were registered via setuptools' legacy `scripts=` keyword, which silently failed to create real, runnable `.exe` commands on Windows (Windows has no shebang support). They're now registered as `console_scripts` entry points instead.
- Fixed thread oversubscription between `multiprocessing.Pool` (one worker process per logical core) and numpy's BLAS backend/OpenCV's internal threading (each defaulting to every logical core *inside* every worker process too), which could make runs on many-core machines slower rather than faster.
- Fixed movie-rendering code (`-om`/`-sm`) that shelled out to the POSIX-only `cp` command with POSIX-only shell quoting, which silently broke on Windows; replaced with cross-platform `subprocess.run`/`shutil.copy`.
- The per-movie summary CSV gains a `pCa` column (populated from a `pCaX`/`pCaX-Y` folder anywhere in a row's path, e.g. `pCa4` -> `4.0`, `pCa4-7` -> `4.7`) and is now named after the **LEVEL1** directory instead of the generic `summary.csv`.
- General dependency, packaging, and warning/noise cleanup, including removing the unused legacy `bin/motility.py` script and trimming unused Python dependencies (`networkx`, `PyWavelets`).
- Fixed a crash (`IndexError` in `make_frame_links`) when a movie's `metadata.txt` has fewer recorded timestamps than image frames (see "Missing frame timestamps" below) - the missing timestamp is now extrapolated instead of crashing the whole analysis run.
- `hill` gains a `-d2` option to fit and plot a second pCa/speed file alongside the first, plus a `-nl` option to normalize each curve to its own 0-1 speed range for shape-only comparisons (see "Hill equation fitting" below). Both `hill` plots now report the fitted speed at pCa50, label curves with a short name truncated to the input filename's first underscore-delimited token (also used for output filenames), and no longer show a separate legend entry for the underlying data points.
- Fixed a crash (`FileNotFoundError` on a missing `.in` file) when a leaf directory has un-exploded raw tif frames (e.g. a MicroManager `Default` acquisition folder that was never run through `stack2tifs`) sitting alongside properly-exploded ones elsewhere in the same batch.
- `fast` now resumes automatically after a crash or interruption, skipping movies (and **LEVEL2/LEVEL3** combined results) that a previous run already finished with the same analysis parameters, instead of reprocessing the whole batch from scratch (see "Resuming after a crash or interruption" below).
- `hill` gains a `-fixmin` option that uses pCa 9 as the zero baseline (implying `-bs`) and fixes `S_min` at exactly 0 in the fit itself (a 3-parameter fit over `S_max`/`Ca50`/`n`), so the fitted curve actually passes through 0 rather than landing only approximately there (see "Hill equation fitting" below).

**No changes were made to the core scientific calculations/algorithms** beyond the bug fixes noted above, which corrected unintended deviations from the original scoring logic rather than introducing new analysis behavior. **You should still cite the original paper by Tural Aksel** (see citation above) if you use this software or its outputs.

If you do not have experience with the command line or Python, this software will be difficult to use, regardless of which OS you're on. As of 7/30/21, Tural Aksel is **no longer responding to questions** about the original FASTrack software, and the maintainer of this fork is likewise not a professional programmer and is not actively maintaining this repository as a supported product. Use everything here at your own risk, and expect to do some of your own troubleshooting.

## Dependencies

Most Python dependencies install automatically via `pip` (see `setup.py` / `requirements.txt`). However, several dependencies are **not** Python packages and must be installed manually at the operating-system level before (or after) installing FAST, because `pip` cannot install them for you:

| Dependency | Why it's needed | Notes |
|---|---|---|
| **ffmpeg** | Used to encode the `-om` overlay tracking movie (`.mp4`) | System binary, not a Python package |
| **Tk / python3-tk** | Used as the GUI backend for `matplotlib` when a display is available | Often bundled with Python on Windows/macOS, but frequently missing on Linux |
| **avconv / libav-tools** | Used by the legacy `-m` skeleton tracking movie (`.avi`) feature | Largely obsolete; most modern systems no longer ship `avconv`. If you only need tracking movies, prefer `-om` (ffmpeg-based) instead |
| **MS-compatible TrueType fonts** | Needed for matplotlib plots to render with expected fonts on Linux | Cosmetic only; plots will still generate without this |

If `pip install` fails with a wheel-build error for one of the Python dependencies (commonly `opencv-python`, `scikit-image`, or `numpy`), it is usually because your system is missing basic C/Python build tools (a C compiler, Python headers, libffi headers). Installing your OS's standard development toolchain packages (see OS-specific instructions below) resolves this in almost all cases.

## Installation

Before installing, remove any previous FASTrack installation and delete any lines referencing `FAST` left over in your shell startup files (`.bashrc`, `.profile`, `.bash_profile`, etc.) by a prior install.

It is **strongly recommended** to install FAST into an isolated virtual environment (via Python's built-in `venv` or via `conda`), rather than into your system/base Python. FAST requires **Python 3.8+**.

Clone the repository first:

```bash
git clone https://github.com/anonymnon/FASTrack.git
cd FASTrack
```

### Linux (Ubuntu/Debian-based)

1. Install system-level build tools and the manual dependencies listed above:
   ```bash
   sudo apt update
   sudo apt install python3-dev python3-venv python3-tk libffi-dev build-essential
   sudo apt install ffmpeg
   sudo apt install ttf-mscorefonts-installer   # optional, for matplotlib font rendering
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv ~/.venvs/FAST
   source ~/.venvs/FAST/bin/activate
   ```
3. Install FAST from the cloned repository:
   ```bash
   pip install --upgrade pip
   pip install .
   ```
4. (Optional) If matplotlib font caching causes display glitches after installing fonts, clear its cache:
   ```bash
   rm -f ~/.cache/matplotlib/fontList.cache
   ```

To use FAST again later, just re-activate the virtual environment: `source ~/.venvs/FAST/bin/activate`.

### macOS

1. Install [Homebrew](https://brew.sh/) if you don't already have it.
2. Install the manual dependencies:
   ```bash
   brew install python@3.11 ffmpeg
   ```
3. Create and activate a virtual environment:
   ```bash
   python3 -m venv ~/.venvs/FAST
   source ~/.venvs/FAST/bin/activate
   ```
4. Install FAST:
   ```bash
   pip install --upgrade pip
   pip install .
   ```

Tk is bundled with the python.org/Homebrew Python builds, so a separate Tk install usually isn't required on macOS.

### Windows

Using a `conda`/Miniconda environment is the most reliable approach on Windows.

1. Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or Anaconda.
2. Open an "Anaconda Prompt" and create an environment:
   ```bat
   conda create -n FAST python=3.11
   conda activate FAST
   ```
3. Install ffmpeg into the same environment via conda-forge:
   ```bat
   conda install -c conda-forge ffmpeg
   ```
4. From the cloned repository directory, install FAST:
   ```bat
   python -m pip install --upgrade pip
   python -m pip install .
   ```
5. Confirm the commands installed correctly:
   ```bat
   stack2tifs
   ```
   This should print a usage/help banner (then exit, since no `-d` directory was given). If Windows instead says `'stack2tifs' is not recognized...`, see **Troubleshooting** below.

Alternatively, if you prefer plain `venv` instead of conda on Windows, install Python from [python.org](https://www.python.org/) (Tk is included by default) and [ffmpeg](https://ffmpeg.org/download.html#build-windows), making sure it's added to your `PATH`. Then:
```bat
python -m venv %USERPROFILE%\venvs\FAST
%USERPROFILE%\venvs\FAST\Scripts\activate
python -m pip install --upgrade pip
python -m pip install .
```

#### Troubleshooting: `fast`/`lima`/`stack2tifs` not found after `pip install .`

On Windows, many machines have more than one Python installed (a conda env, python.org, the Microsoft Store stub, etc.), and they can shadow each other's `pip` on `PATH`. If you run `pip install .` and the bare `pip` command happens to resolve to a *different* Python than the one in your active conda/venv environment, FAST gets installed into the wrong place and the commands won't be on `PATH` for the environment you're using.

Always prefer `python -m pip install .` over bare `pip install .` — this guarantees pip installs into the same Python that the `python` command resolves to. To check what your activated environment's `pip` actually points at:
```bat
python -m pip --version
```
The printed path should be inside your conda/venv environment's folder (e.g. `...\envs\FAST\Lib\site-packages\pip` or `...\venvs\FAST\Lib\site-packages\pip`). If it points somewhere else, your environment doesn't have `pip` installed in it — for conda, run `conda install pip` inside the activated environment first, then retry `python -m pip install .`.

### Re-installing after pulling updates or applying a patch

`pip install .` (without `-e`) makes a snapshot copy of the code into your environment. If you pull new commits, apply a patch, or edit the source yourself, re-run the install so the changes take effect:
```bash
pip install --force-reinstall --no-deps .
```
If you'd rather have your installed environment automatically reflect any source edits without reinstalling, use an editable install instead: `pip install -e .`

After installation, don't move the `FASTrack` directory to a different location without reinstalling.

**Windows users upgrading from an older FASTrack install:** versions prior to v2.0.0 registered `fast`/`lima`/`stack2tifs` using a packaging method that didn't reliably create a working command on Windows. If you previously worked around this, or have a stale install lying around, run `python -m pip install --force-reinstall --no-deps .` to pick up the fix.

## Preparation of movie files

- **fast** only analyzes movie tif files recorded using [micro-manager](https://www.micro-manager.org/). For movies recorded using other software, first save the movie as tiff stacks and convert the stacks to micro-manager output format using one of the stack-conversion scripts below.

- **stack2tifs** takes a directory containing an image stack, explodes the stack into individual frames, contrast-stretches each frame (percentile-based, pure Python - no ImageJ/Java required), and writes frames with names compatible with the rest of the FAST toolchain. If the source directory contains a `*_metadata.txt` file (where `*` matches the image's base filename) and the `-t` flag is given, elapsed frame times are extracted from that file and written into a FAST-compatible metadata file. If no such metadata file exists, omit `-t` and the program will instead generate elapsed times from the `-f` frame-rate argument.
   ```
   stack2tifs -d DIRECTORY -f FRAMERATE -s SIZELOWERBOUND -t USE_METADATA_FILE -o OVERWRITE
   ```

- **DIRECTORY** is the top directory in which tiff stacks are stored.
- **FRAMERATE** is the frame rate of the movies in frames per second **(Default: 1)**. Process movies with different frame rates separately.
- **SIZELOWERBOUND** is the lower bound for the size (Mbytes) of the tiff stacks to be converted into individual tiffs **(Default: 6)**. Only tiff stacks bigger than SIZELOWERBOUND are processed.
- **OVERWRITE**: if a stack has already been exploded into individual frames in a previous run, `stack2tifs` skips it and prints a notice by default. Pass `-o yes` to force re-exploding/overwriting those frames instead (also prints a notice). **(Default: no)**.

- **Missing frame timestamps**: occasionally a movie's `metadata.txt` ends up with fewer `ElapsedTime-ms` entries than it has image frames - a micro-manager quirk where the last frame's image gets saved but its timestamp never gets written (usually because acquisition was stopped right at the end). When **fast** needs a timestamp beyond the end of what was recorded, it extrapolates one using the average interval between the timestamps that *were* recorded, rather than failing. This only ever affects the frame(s) missing a timestamp - every other frame pair still uses its real, recorded elapsed time.

## Analysis of movies using FAST

- Although not necessary, it is recommended to organize the movies to be analyzed in a hierarchical order.
   - LEVEL1 (e.g. date)
       - LEVEL2 (e.g. slide number)
            - LEVEL3 (e.g. experimental condition)
                - LEVEL4 (e.g. replicates)

- All **fast** needs is the top directory the movie folders are located at.
    ```
    fast -d LEVEL1
    ```

- **FAST** first finds the lowest LEVEL directories that have movie folders under **LEVEL1**, and analyzes them in order. The lowest level movies (folders) under the same directory are treated as replicates. The results from replicates are combined to determine the average results. Therefore, it is important that the replicates have identical frame rates. Please check example movie files in the **examples/unloaded_motility** directory.

- **FAST** accepts various parameters for comprehensive analysis of filament velocities and for display of results.

    **General/output parameters:**
    - ``` -n  WINDOWSIZE ``` : Number of consecutive frames to average over when computing a smoothed instantaneous velocity for each point along a path **(Default:5)**.
    - ``` -p  PATHLENGTH ``` : Minimum number of linked frames a filament's path must have to be included in the analysis. Filters out short, unreliable tracks **(Default:5)**.
    - ``` -pt TOLERANCE``` : Percent tolerance, given as a whole-number percentage (e.g. `30` for 30%), used to filter out points whose velocity fluctuates too much (standard deviation relative to the mean) within the averaging window from `-n`. A higher value keeps more (noisier) points **(Default:None, i.e. no filtering)**.
    - ```-cl COLOR```: Matplotlib color name/code used for the maximum-velocity data points in the length-vs-velocity scatter plot **(Default:blue)**.
    - ```-fx FUNCTION```: Curve to fit to the maximum-velocity-vs-length data. `exp` fits a single exponential decay (coupling) model, `uyeda` fits the Uyeda length-velocity equation, and `none` skips curve fitting **(Default:none)**.
    - ```-px PIXEL```: Pixel size of the camera/microscope setup, in nanometers. Used to convert all pixel-based measurements (distance, length, velocity) into physical units **(Default:80.65)**.
    - ```-ymax YMAX```: Maximum velocity (nm/s) shown on the y-axis of the scatter plot **(Default:1500)**.
    - ```-xmax XMAX```: Maximum filament length (nm) shown on the x-axis of the scatter plot **(Default:10000)**.
    - ```-maxd MAXD```: Maximum allowed center-of-mass displacement (in nm) for the same filament between two adjacent frames; candidate links farther apart than this are never considered the same filament **(Default: 10x the `-px` pixel size)**.
    - ```-minv MINV```: Minimum average path velocity (nm/s) for a filament's path to be considered "moving" rather than stuck. Paths averaging below this are classified as stuck and given zero velocity in some outputs **(Default: equal to the `-px` pixel size)**.
    - ```-m```: Generate a legacy frame-by-frame tracking movie (`.avi`, via `avconv`) showing reconstructed skeletons and motion arrows.
    - ```-om```: Generate an overlay tracking movie (`.mp4`, via `ffmpeg`) compositing each raw frame onto the `paths_2D.png` tracking background. Filament pixels are rendered black and opaque (darkened proportionally to their brightness), while non-filament background pixels are left fully transparent, so the path-trajectory arrows underneath remain clearly visible.
    - ```-ofps FPS```: Frame rate for the `-om` overlay movie **(Default:5)**.
    - ```-sm```: Generate a movie of just the skeletonized filaments (`.mp4`, via `ffmpeg`), with no trajectory arrows. Filaments belonging to a path classified as stuck (see `-minv`) are drawn in red for every frame that path spans; all other filaments are drawn in the default color.
    - ```-sfps FPS```: Frame rate for the `-sm` skeleton movie **(Default:5)**.
    - ```-r```: Recalculate velocities from previously-saved per-frame filament data, skipping image re-processing (fast iteration on a new parameter set).
    - ```-f```: Force a full re-analysis from the raw images, ignoring any cached per-frame/link data.

- **Resuming after a crash or interruption**: if **fast** is stopped partway through a large batch (crash, `Ctrl+C`, power loss, etc.), simply re-running the exact same command picks up where it left off, rather than reprocessing everything from scratch. Each movie folder that already has a complete result (`paths_2D.png` plus its length-velocity data, produced with the same analysis-affecting parameters as this run) is detected and reused instead of re-extracted/re-linked, printing `Already analyzed ... - resuming past it` instead of `Processing tif files in ...`; the same applies to each **LEVEL2/LEVEL3** combined result once every movie under it has been resumed or (re)analyzed. This reuse only ever applies to parameters that affect the underlying analysis itself (`-px`, `-n`, `-maxd`, `-minv`, `-oscore`, `-lascore`, `-dlascore`) - changing one of those, or passing `-f`/`-r`, forces a full re-analysis instead of silently mixing results from two different settings.

    **Filament-linking score cutoffs (advanced - only change these if you understand the scoring algorithm in [Aksel et al. 2015][1]):**
    - ```-oscore OSCORE```: Overlap-score cutoff. The overlap score measures how directionally/spatially consistent a candidate filament match is between two frames; candidates with an absolute overlap score at or below this cutoff are rejected as a match **(Default:0.4)**.
    - ```-lascore LASCORE```: Log-area-score cutoff. The (log10) area score measures how similar in size/shape two candidate filament detections are; candidates whose log-area score is at or above this cutoff (i.e. too dissimilar in area) are rejected **(Default:1.0)**.
    - ```-dlascore DLASCORE```: Difference-log-area-score cutoff. When more than one candidate in the next frame could plausibly match a given filament, this is the minimum log-area-score gap required between the best and second-best candidate for the match to be accepted unambiguously. If two candidates are too close in score, the (ambiguous) link is rejected rather than guessed at **(Default:0.5)**.

- To estimate maximum velocities TOP5% and PLATEAU, the following parameter set is recommended.
    - ``` fast -n 5 -p 10 -pt 20 -d LEVEL1```
- For loaded motility experiments, the following parameter set is recommended.
    - ``` fast -n 5 -p 10 -d LEVEL1 ```
- Analysis results are stored in **outputs/LEVEL1** in the path FAST is executed, where **LEVEL1** is just the name of the top directory passed to ```-d``` (the parameter-set suffix that earlier versions appended, e.g. ```_n_5_p_10_pt_20```, has been removed so output paths stay short and don't break on Windows). If ```outputs/LEVEL1``` already exists from a previous run, the new run is written to ```outputs/LEVEL1-2``` instead (then ```-3```, ```-4```, etc. on subsequent runs), so re-running **fast** with different parameters never overwrites a previous run's results. Combined results from replicates at the lowest level (LEVEL4) are stored in a subfolder called **combined**.

- Output filenames (e.g. ```*_length_velocity.png```, ```*_full_length_velocity.txt```) are prefixed starting from **LEVEL1** onward (```LEVEL1_LEVEL2_LEVEL3_LEVEL4_...```), rather than the full input path - this keeps filenames short even when the movies are nested deep inside a long input path.

- To analyze the movies with a new parameter set, use ```-r``` flag for speedy analysis.
    - ```fast -r -n 10 -p 10 -pt 20 -d LEVEL1```
- To force re-analyze the movies by processing through individual images, use ``` -f ``` flag.
   -  ```fast -f -n 10 -p 10 -pt 20 -d LEVEL1```

 - To make tracking movies, use ``` -m ``` flag (legacy, `.avi` via `avconv`) or ```-om``` flag (recommended, `.mp4` via `ffmpeg`).

     - ``` fast -m -n 10 -p 10 -pt 20 -d LEVEL1```
     - ``` fast -om -n 10 -p 10 -pt 20 -d LEVEL1```

- To abort execution, press ```CTRL+C``` on terminal.

- Please check the examples in **examples/unloaded_motility** to get familiar with **stack2tifs** and **fast**.

## Result descriptions

- **fast** plots velocities as png files and prints velocity data as text files. Complete list of unfiltered velocity points are saved with the extension ```*_full_length_velocity.txt```. Maximum path velocities, which are colored in the scatter plot, are saved with the extension ```*_max_length_velocity.txt```. The plots are saved with the extension ```*_length_velocity.png```. Combined results are saved in ```combined``` folder in ```outputs``` directory.

- First column in ```*_length_velocity.txt``` files is the filament length in nm. Second column is the mean velocity over the ```n``` frame window (see above -n WINDOWSIZE). Third column is the standard deviation of velocities within ```n``` frame window. Fourth column is the length of the track from which the velocity is measured.
- For description of ```*_length_velocity.png``` and the algorithms of **fast**, see [**Aksel et al. 2015**][1]

- ```*_paths_2D.png``` shows the tracks for each filament ad the number is the average velocity for each filament track in nm/s.

- Tracking movies are saved as ```*_filament_tracks.avi``` if ```-m``` is used, or ```overlay_movie.mp4``` if ```-om``` is used, in fast execution. Please remember that movies will be generated only if the packages required for movie generation (`avconv` or `ffmpeg`, respectively) are installed.

[1]: http://www.cell.com/cell-reports/abstract/S2211-1247(15)00381-2

- In addition, mean and standard error of mean (SEM) for the velocity parameters are stored in **MEAN_values.txt** and **SEM_values.txt** in **combined** folder.

- A summary CSV file, named after the **LEVEL1** directory (e.g. ```LEVEL1.csv```, not the generic ```summary.csv```), is also generated for each run, with one row per processed movie (labeled by its **LEVEL2_LEVEL3_LEVEL4** path, e.g. ```CaMy1_Rep1_1_1_MMStack_Pos0.ome```) and columns for ```pCa```, ```TOP5%``` velocity, filtered/unfiltered ```MVEL```, percent of stuck filaments, mean/standard-deviation/skewness of the filtered filament lengths (```FIL-LENGTH```), and every user-adjustable parameter value used for that run (```-px```, ```-p```, ```-n```, ```-pt```, ```-ymax```, ```-xmax```, ```-cl```, ```-fx```, ```-maxd```, ```-minv```, ```-oscore```, ```-lascore```, ```-dlascore```, ```-ofps```, ```-sfps```, ```-m```, ```-om```, ```-sm```, ```-f```, ```-r```). The ```pCa``` column is populated from a ```pCaX``` or ```pCaX-Y``` folder anywhere in that row's path (```X```,```Y``` integers), e.g. a path containing ```pCa4``` gives ```4.0```, and ```pCa4-7``` gives ```4.7```; rows with no such folder are left blank. A copy is written both to the **LEVEL1** input directory and to the top of the corresponding **outputs/LEVEL1** (or ```outputs/LEVEL1-2```, etc.) folder.

## Hill equation fitting for pCa vs. speed data

- The **hill** command fits a 4-parameter Hill equation to pCa vs. speed data and reports the fitted parameters with 95% confidence intervals.

- Provide a CSV or Excel (`.xlsx`/`.xls`) file that contains at minimum a column of pCa values and a column of speed values. If multiple rows share the same pCa value they are averaged before fitting.

    ```
    hill -d FILE [-c SPEED_COLUMN] [-p PCA_COLUMN] [-bs] [-fixmin]
    ```

    - **FILE** (`-d`): path to the CSV or Excel input file **(required)**.
    - **SPEED_COLUMN** (`-c`): name of the speed column in the file **(Default: `speed`)**.
    - **PCA_COLUMN** (`-p`): name of the pCa column in the file **(Default: `pCa`)**.
    - **`-bs`**: subtract the mean speed at pCa 9 from all speed values before fitting, so the baseline (no-calcium) speed is forced to zero. Note this only zeroes that one data point - the fitted curve's own `S_min` is still a free parameter and can land slightly away from 0 (e.g. -3.3 nm/s) even after this shift **(Default: off)**.
    - **`-fixmin`**: use pCa 9 as the zero baseline (this implies `-bs`, even if `-bs` isn't separately given - fixing the curve at 0 without first re-centering the data around a true zero would distort every other fitted parameter) and fix `S_min` at exactly 0 in the fit itself (a 3-parameter fit over `S_max`/`Ca50`/`n` instead of 4), so the fitted curve actually passes through 0 rather than landing only approximately there **(Default: off)**.

- To compare two conditions on the same graph, pass a second file with `-d2`. Each file is still fit independently (its own Hill curve, its own reported parameters), but both are drawn on one plot and reported in one text file:

    ```
    hill -d FILE1 -d2 FILE2 [-c2 SPEED_COLUMN2] [-p2 PCA_COLUMN2] [-col1 COLOR1] [-col2 COLOR2] [-bs] [-nl] [-fixmin]
    ```

    - **FILE2** (`-d2`): path to a second CSV or Excel input file, fit and plotted alongside `-d` **(optional - omitting it runs the original single-file behavior)**.
    - **SPEED_COLUMN2** / **PCA_COLUMN2** (`-c2`/`-p2`): column names for `-d2`, in case it doesn't share the same column names as `-d` **(Default: same as `-c`/`-p`)**.
    - **`-bs`** applies to both files when `-d2` is given, and is ignored (with a notice) if `-nl` is also given.
    - **COLOR1** / **COLOR2** (`-col1`/`-col2`): line and marker color for `-d` and `-d2` respectively **(Default: `black` for `-d`, `red` for `-d2`)**.
    - **`-nl`**: normalize each curve to its own speed range before fitting/plotting - see "Normalized graphs" below.
    - **`-fixmin`** applies to both files when `-d2` is given.

- The 4-parameter Hill equation used is:

    > Speed = S_min + (S_max − S_min) × Ca^n / (Ca50^n + Ca^n)

    where Ca = 10^(−pCa). The four fitted parameters are **S_min** (minimum speed), **S_max** (maximum speed), **Ca50** (the calcium concentration at half-maximal activation), and **n** (the Hill cooperativity coefficient). **pCa50** (= −log₁₀Ca50) is derived from Ca50 and reported with its own 95% CI via error propagation. The **speed at pCa50** (the curve's midpoint, exactly (S_min + S_max) / 2 regardless of Ca50/n) is reported alongside the fitted parameters, in the plot legend, and with its own 95% CI in the text file where the covariance between S_min and S_max makes that computable.

- The plot legend only ever shows the fitted curve(s), labeled with a short name plus the fit summary (e.g. `WT: pCa50=... n=... R²=... Smax=... S(pCa50)=...`), not a separate entry for the underlying data points - the averaged data points are still drawn on the plot, just unlabeled. The short name is the input filename truncated to whatever comes before its first underscore (e.g. `WT_pCa_speed_extraSlides.csv` → `WT`), so descriptive input filenames don't clutter the legend. The legend itself is placed below the plot area so it never overlaps the data/curves or narrows the plot.

- Outputs are written to the same folder as the first input file, named using that same short, truncated name(s):
    - Single-file (`-d` only), e.g. `WT_pCa_speed_extraSlides.csv`: `WT.txt` / `.pdf` / `.png`.
    - Two-file comparison (`-d` + `-d2`), e.g. `WT_pCa_speed_extraSlides.csv` and `E239G_pCa_speed_extraSlides.csv`: `WT_E239G.txt` / `.pdf` / `.png`.
    - The `.txt` file contains fitted parameters with 95% confidence intervals (including speed at pCa50), R², RMSE, and the averaged data table - one such block per file when comparing two.
    - The `.pdf` / `.png` show the averaged data points with the fitted Hill curve(s) overlaid. The pCa x-axis is inverted (high pCa on the left) following the standard convention.

- **Normalized graphs (`-nl`)**: rescales each curve's speed values to its own [0, 1] range (that curve's own minimum → 0, own maximum → 1) before fitting and plotting - useful for comparing the *shape* of two curves (pCa50, cooperativity) side by side without their absolute speeds (which can differ a lot between conditions) dominating the comparison. Each curve is normalized independently: if `WT` has a maximum of 500 nm/s and `E239G` has a maximum of 1000 nm/s, both still scale to 1.0 on their own curve. Since normalization already forces each curve's own baseline to 0, `-bs` is ignored (with a printed notice) whenever `-nl` is given. Output filenames get a `_nl` suffix, e.g. `WT_E239G_nl.txt` / `.pdf` / `.png`, and the `.txt` file reports the fit in these same normalized (unitless, 0-1) terms rather than nm/s.

## Loaded in vitro motility analysis

- FAST is designed for high throughput analysis of loaded in vitro motility movies. For the experimental setup and the details of the loaded motility analysis please read through [our paper][1].

[1]: http://www.cell.com/cell-reports/abstract/S2211-1247(15)00381-2

- To extract the "force" parameter from a set of data collected at different utrophin (or any other actin binding protein) concentrations, use the python script called **lima**. LIMA stands for Loaded In vitro Motility Analysis.

- To use lima for loaded motility analysis, user has to name the movie files in a specific format.

- **LEVEL3** (described above) should be minimally named in the following way ```PROTEINNAME_XnM_utr```. ```X``` is the utrophin concentration. For example, for a movie recorded at 0.5 nM utrophin for a myosin called **alpha**, the LEVEL3 folder would be named ```alpha_0.5nM_utr```. For LEVEL3 and hierarchical organization of the movie folders, see above. For an example set of loaded motility data, check under ```examples/loaded_motility``` directory.

- To run **lima**, on a set of movies processed by **fast**, first go to outputs directory where the results for the complete data set are stored. For example, if user is in ```examples/loaded_motility```, enter in terminal ```cd outputs``` to change directory to outputs.

- To perform a loaded motility analysis for a **FOLDER** in ```outputs``` directory, enter in terminal,
    - ```lima -d FOLDER```
- Analysis results will be stored in ```FOLDER/combined/lima```.

- For the analysis of an example data set, check ```examples/loaded_motility```.
    - First, analyze the movies:
        - ```fast -r -d 032714```
    - Move to outputs folder:
        - ```cd outputs```
    - Process the only directory in **outputs**:
        - ```lima -d 032714__pt_none__n_5__ymax_1500__p_5__fx_none```
    - Check the analysis results under
        - ```032714__pt_none__n_5__ymax_1500__p_5__fx_none/combined/lima```.

- For different analysis options, enter ```lima -h```.

## FAQ

- For questions and to report bugs in the **original** FASTrack software, the original author's contact is turalaksel[at]gmail.com - however, as of 7/30/21, Tural Aksel is no longer responding to questions about this program. This fork's maintainer is reachable at anonymnon[at]gmail.com but is not a professional programmer and does not actively maintain this repository as a supported product; please expect to do your own troubleshooting.
