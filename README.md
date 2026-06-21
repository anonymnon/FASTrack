# FAST v2.0.0-alpha.1: Fast Automated Spud Tracker

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
- General dependency, packaging, and warning/noise cleanup.

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
   pip install --upgrade pip
   pip install .
   ```

Alternatively, if you prefer plain `venv` instead of conda on Windows, install Python from [python.org](https://www.python.org/) (Tk is included by default) and [ffmpeg](https://ffmpeg.org/download.html#build-windows), making sure it's added to your `PATH`. Then:
```bat
python -m venv %USERPROFILE%\venvs\FAST
%USERPROFILE%\venvs\FAST\Scripts\activate
pip install --upgrade pip
pip install .
```

### Re-installing after pulling updates or applying a patch

`pip install .` (without `-e`) makes a snapshot copy of the code into your environment. If you pull new commits, apply a patch, or edit the source yourself, re-run the install so the changes take effect:
```bash
pip install --force-reinstall --no-deps .
```
If you'd rather have your installed environment automatically reflect any source edits without reinstalling, use an editable install instead: `pip install -e .`

After installation, don't move the `FASTrack` directory to a different location without reinstalling.

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
    - ```-r```: Recalculate velocities from previously-saved per-frame filament data, skipping image re-processing (fast iteration on a new parameter set).
    - ```-f```: Force a full re-analysis from the raw images, ignoring any cached per-frame/link data.

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

- A **summary.csv** file is also generated for each run, with one row per processed movie (labeled by its **LEVEL2_LEVEL3_LEVEL4** path, e.g. ```CaMy1_Rep1_1_1_MMStack_Pos0.ome```) and columns for ```TOP5%``` velocity, filtered/unfiltered ```MVEL```, percent of stuck filaments, mean/standard-deviation/skewness of the filtered filament lengths (```FIL-LENGTH```), and every user-adjustable parameter value used for that run (```-px```, ```-p```, ```-n```, ```-pt```, ```-ymax```, ```-xmax```, ```-cl```, ```-fx```, ```-maxd```, ```-minv```, ```-oscore```, ```-lascore```, ```-dlascore```, ```-ofps```, ```-m```, ```-om```, ```-f```, ```-r```). A copy is written both to the **LEVEL1** input directory and to the top of the corresponding **outputs/LEVEL1** (or ```outputs/LEVEL1-2```, etc.) folder.

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
