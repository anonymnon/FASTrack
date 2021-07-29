import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="FASTrack",# Replace with your own username
    version="1.0.2",
    author="Ankit Garg",
    author_email="anonymnon@gmail.com",
    description="Companion script for FASTrack and additional debuggin of original program",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anonymnon/FASTrack",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    scripts=['bin/fast',
             'bin/lima',
             'bin/stack2tifs',
             'bin/stack2tifspy3'],
    install_requires=['backports.functools-lru-cache==1.5',
                      'cycler==0.10.0',
                      'decorator==4.3.0',
                      'enum34==1.1.6',
                      'futures==3.2.0',
                      'imageio==2.3.0',
                      'kiwisolver==1.0.1',
                      'matplotlib==2.2.2',
                      'networkx==2.1',
                      'numpy==1.11.2',
                      'opencv-python==3.4.0.12',
                      'pillow>=6.2.2',
                      'pyparsing==2.2.0',
                      'python-dateutil==2.7.2',
                      'pytz==2018.4',
                      'PyWavelets==0.5.2',
                      'scikit-image==0.13.1',
                      'scipy==1.0.1',
                      'six==1.11.0',
                      'subprocess32==3.2.7'],
    python_requires='>=3.*',
)
