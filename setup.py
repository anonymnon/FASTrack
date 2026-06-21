import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="FASTrack",
    version="1.0.2",
    author="Tural Aksel",
    author_email="turalaksel@gmail.com",
    description="Automated filament tracker for in-vitro motility actin gliding assays",
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
    install_requires=['cycler>=0.11.0',
                    'decorator>=5.1.1',
                    'imageio>=2.31.0',
                    'kiwisolver>=1.4.4',
                    'matplotlib>=3.7.0',
                    'networkx>=3.1',
                    'numpy>=1.24.0',
                    'opencv-python>=4.8.0',
                    'pillow>=9.5.0',
                    'pyparsing>=3.0.9',
                    'python-dateutil>=2.8.2',
                    'pytz>=2023.3',
                    'PyWavelets>=1.4.1',
                    'scikit-image>=0.21.0',
                    'scipy>=1.10.0',
                    'six>=1.16.0',
                    'tifffile'],
    python_requires='>=3.8',
)
