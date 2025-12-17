# FAST v1.0.1a1: Fast Automated Spud Tracker

Please cite [**Aksel T, Yu EC, Sutton S, Ruppel KM, Spudich JA. Cell Reports. 2015. Ensemble force changes that result from human cardiac myosin mutations and a small molecule effector.**][1]

[1]: http://www.cell.com/cell-reports/abstract/S2211-1247(15)00381-2

**examples** folder containing all example movies can be downloaded from https://goo.gl/87LyDG

&copy; 2020 Tural Aksel

## Foreword
This version of FASTrack is a minor update to Tural Aksel's original program to fix some issues I was having in my Ubuntu 20.04 OS in addition to adding a new **stack2tifs** script called **stack2tifspy3** that allows for a bit more automated processing of images that were captured by Micro-manager open source microscope software. There was no alteration to the underlying calculations that were done by the original software. Furthermore, the original software is fully operational after some minor debugging (which may include editing some of the source code). Thus, you should cite the original paper by Tural Aksel if you use this repository.

If you do not have experience with Linux or Python, this software may be difficult to use. Though the hope is that anybody can run this software under any Linux machine, it will very likely not work as-is without some effort on the user's end to try to troubleshoot the software. As of 7/30/21, Tural Aksel does not seem to be answering any further questions on his original FASTrack software. You are welcome to contact me with any bugs at anonymnon@gmail.com but realize that I am not a programmer nor am I planning to actively maintain this repository. Also, all the instructions provided below are for Linux. I found MacOS to be too cumbersome.

## Dependencies

There are several packages that either do not seem to install properly or are not a part of the original installation. Installing the following packages helped me to avoid errors, but you will likely need to troubleshoot your own environment. For those unfamiliar with Linux, please realize that any `sudo` command will result in running in executing something as a super user. USE AT YOUR OWN RISK. It is very possible to break your Linux installation.

### Installing virtualenv and virtualenvwrapper

Install virtualenv by running `sudo apt install virtualenv`

Install virtualenvwrapper by running `sudo apt install virtualenvwrapper`


**NOTE** I often get an error when trying to call virtualenvwrapper because it does not seem to get added to my PATH by default. If you want to be able to call virtualenvwrapper by typing 'mkvirtualenv', find where virtualenvwrapper was installed (for me it was `/usr/share/virtualenvwrapper/virtualenvwrapper.sh`), and add the following to your `~/.bash_profile`:

```
#Executing source command to allow mkvirtualenv command
source "/usr/share/virtualenvwrapper/virtualenvwrapper.sh"
```

To manually activate the bash profile without closing the terminal, execute the following command:
`source ~/.bash_profile`

### Installing ImageJ for use of stack2tifspy3
Several packages are required for ImageJ. Whether in your virtual environment or outside your virtual environment, install the following:

```
$sudo apt-get install openjdk-11-jdk
$sudo apt install maven
```

### Misc
I often ran into the following error during installation of FAST: `Failed building wheel for subprocess32`

This was solved by installing multiple python basic packages:
```
sudo apt install python-dev
sudo apt install libffi-dev
sudo apt install build-essential
```

If you get the following error: `ImportError: No module named _tkinter, please install the python-tk package`, Do the following:
`sudo apt install python-tk`

This version of the program requires GNU-parallel. Please make sure it is installed:
`sudo apt-get install parallel`

To generate movies of tracking, install avconv package:
`sudo apt-get install ffmpeg`.

To display fonts properly on Ubuntu, install MS fonts.
  
`$sudo apt-get install ttf-mscorefonts-installer`

On Ubuntu, after installing MD fonts, remove font cache file for matplotlib in your home directory.
    
`$rm -f ~/.cache/matplotlib/fontList.cache`

## Installation

Before you install this package, remove previous installations and make sure to delete any lines with `FAST` in `.bashrc`, '`.profile` or `.bash_profile` files in your home directory (`~`).  

### Installing FAST to python 2.7 environment
Installing this package inside python virtual environment is highly encouraged. After installing `virtualenv` and `virtualenvwrapper`, create a python2 virtual environnment.

Create a virtual environment with python2.7.

`$mkvirtualenv FAST -p python2.7$`

Remember to activate the virtual environment

`$workon FAST`

To install the FAST package, clone this repository and extract into the directory of your choice. Within the directory, execute the following command:

`$(FAST) pip install FASTrack` 

This particular version is only managed through github. Clone the repository through github or install github to your computer. The original/master version can be found at  [FASTrack](https://github.com/turalaksel/FASTrack/tree/master/FAST). 

`$(FAST) pip install .` 

Everytime you need to use `FAST`, remember to activate `FAST` virtual environment typing `workon FAST` on terminal.

### Installing FAST to python 3 environment to use stack2tifspy3
To run **stack2tifspy3**, you will need to create a Python3 virtual environment and install the ImageJ module. Create a python3 virtual environment:

`$mkvirtualenv FAST3 -p python3$`

Remember to activate the virtual environment if you are not on it already.

`$workon FAST3`

Go to your FAST directory and install the package

`$(FAST3) pip install .`

Inside your Python3 virtual environment:

`$(FAST3) pip install pyimagej`

After installation don't move the FAST directory to some other location.

## Preparation of movie files

- **fast** only analyzes movie tif files recorded using  [micro-manager](https://www.micro-manager.org/). For movies, recorded using other software, first save the movie as tiff stacks and convert the stacks to micro-manager output format using **stack2tiffs**.
   
     ```
    stack2tifs -d DIRECTORY -f FRAMERATE -s SIZELOWERBOUND
     ```

- (Update by Ankit 7/27/2021) The prior stack2tifs script did not universally handle files captured from Micromanager. The updated stack2tifspy3 takes a directory containing an image stack, explodes the stack into individual frames, autoenhances the images using ImageJ, and saves the new frame with names that are compatible with the original FAST program. If the directory contains a *_metadata.txt file where * = the exact same name as the image and the "-t" parameter is given any argument; the elapsed times will be extracted and written to a new metadata file that is compatible with the original FAST program. If no metadata file exists, do not use the "-t" argument and the program will write a metadata file based on the frame rate provided by the "-f" argument. THIS SCRIPT MUST BE RUN UNDER A PYTHON3 ENVIRONMENT since the ImageJ module requires Python 3. Recommend creating a Python3 environment, running this script, then switching back to a Python 2.7 environment to continue the analysis. FAST WILL NOT WORK UNDER PYTHON3.
   
     ```
    stack2tifspy3 -d DIRECTORY -f FRAMERATE -s SIZELOWERBOUND -t USE_METADATA_FILE
     ```

- **DIRECTORY** is the top directory in which tiff stacks are stored.
- **FRAMERATE** is the frame rate of the movies in frame per second **(Default: 1)**. Process movies with different frame rates separately.
- **SIZELOWERBOUND** is the lower bound for the size (Mbytes) of the tiff stacks to be converted into individual tiffs **(Default: 6)**. Only tiffstacks bigger in size than SIZELOWERBOUND are processed.

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
    - ``` -n  WINDOWSIZE ``` : Number of consecutive frames for velocity averaging **(Default:5)**.
    - ``` -p  PATHLENGTH ``` : Minimum length for the tracked filament paths in the analysis **(Default:5)**.
    - ``` -pt TOLERANCE``` : Percent tolerance parameter to filter fluctuating velocities **(Default:None)**.
    - ```-cl COLOR```: Color of the data points in velocity scatter plot **(Default:blue)**.
    - ```-fx FUNCTION```: Function to be fitted to maximal velocity data. **exp** for single exponential decay, **uyeda** for Uyeda equation and **none** for no curve fitting **(Default:none)**.
    - ```-px PIXEL```: Pixel size in nm **(Default:80.65)**.  
    - ```-ymax YMAX```: Maximum velocity in nm/s for the scatter plot **(Default:1500)**.
    - ```-xmax XMAX```: Maximum filament length in nm for the scatter plot **(Default:10000)**.
    - ```-mv MV```: Maximum allowed distance in nm between adjacent frames for a filament (Default:2016.25)

- To estimate maximum velocities TOP5% and PLATEAU, I recommend the following parameter set.
    - ``` fast -n 5 -p 10 -pt 20 -d LEVEL1```
- For loaded motility experiments, I recommend the following parameter set.
    - ``` fast -n 5 -p 10 -d LEVEL1 ```
- Analysis results are stored in **outputs** folder in the path FAST is executed. Analysis results with different parameter sets are stored in different folders. For example, the results for **LEVEL1** analyzed using the parameters ``` -n 5 -p 10 and -pt 20``` are stored in **outputs/LEVEL1_n_5_p_10_pt_20**. Combined results from replicates at the lowest level (LEVEL4) are stored in a subfolder called **combined**.

- To analyze the movies with a new parameter set, use ```-r``` flag for speedy analysis.
    - ```fast -r -n 10 -p 10 -pt 20 -d LEVEL1```
- To force re-analyze the movies by processing through individual images, use ``` -f ``` flag.
   -  ```fast -f -n 10 -p 10 -pt 20 -d LEVEL1```
 
 - To make tracking movies, use ``` -m ``` flag.
 
     - ``` fast -m -n 10 -p 10 -pt 20 -d LEVEL1```   

- To abort execution, press ```CTRL+C``` on terminal.

- Please check the examples in **examples/unloaded_motility** to get familiar with **stack2tiffs** and **fast**.

## Result descriptions

- **fast** plots velocities as png files and prints velocity data as text files. Complete list of unfiltered velocity points are saved with the extension ```*_full_length_velocity.txt```. Maximum path velocities, which are colored in the scatter plot, are saved with the extension ```*_max_length_velocity.txt```. The plots are saved with the extension ```*_length_velocity.png```. Combined results are saved in ```combined``` folder in ```outputs``` directory.   

- First column in ```*_length_velocity.txt``` files is the filament length in nm. Second column is the mean velocity over the ```n``` frame window (see above -n WINDOWSIZE). Third column is the standard deviation of velocities within ```n``` frame window. Fourth column is the length of the track from which the velocity is measured. 
- For description of ```*_length_velocity.png``` and the algorithms of **fast**, see [**Aksel et al. 2015**][1] 

- ```*_paths_2D.png``` shows the tracks for each filament ad the number is the average velocity for each filament track in nm/s.

- Tracking movies are saved as ```*_filament_tracks.avi``` if ```-m``` is used in fast execution. Please remember that movies will be generated, if only the packages required for movie generation are installed.

[1]: http://www.cell.com/cell-reports/abstract/S2211-1247(15)00381-2

- In addition, mean and standard error of mean (SEM) for the velocity parameters are stored in **MEAN_values.txt** and **SEM_values.txt** in **combined** folder.

## Loaded in vitro motility analysis

- FAST is designed for high throughput analysis of loaded in vitro motility movies. For the experimental setup and the details of the loaded motility analysis please read through [our paper][1].

[1]: http://www.cell.com/cell-reports/abstract/S2211-1247(15)00381-2

- To extract the "force" parameter from a set of data collected at different utrophin (or any other actin binding protein) concentrations, I wrote a python script called **lima**. LIMA stands for Loaded In vitro Motility Analysis.

- To use lima for loaded motility analysis, user has to name the movie files in a specific format.

- **LEVEL3** (described above) should be minimally named in the following way ```PROTEINNAME_XnM_utr```. ```X``` is the utrophin concentration. For example, for a movie recorded at 0.5 nM utrophin for a myosin called **alpha**, I would name the LEVEL3 folder as ```alpha_0.5nM_utr```. For LEVEL3 and hierarchical organization of the movie folders, see above. For an example set of loaded motility data, check under ```examples/loaded_motility``` directory.

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

- For questions and to report bugs, please contact me by turalaksel[at]gmail.com.
