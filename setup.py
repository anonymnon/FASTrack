import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="FASTrack",
    version="2.0.0",
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
    entry_points={
        'console_scripts': [
            'fast=FAST.cli_fast:main',
            'hill=FAST.cli_hill:main',
            'lima=FAST.cli_lima:main',
            'stack2tifs=FAST.cli_stack2tifs:main',
        ],
    },
    install_requires=['cycler>=0.11.0',
                    'decorator>=5.1.1',
                    'imageio>=2.31.0',
                    'kiwisolver>=1.4.4',
                    'matplotlib>=3.7.0',
                    'numpy>=1.24.0',
                    'opencv-python>=4.8.0',
                    'openpyxl>=3.1.0',
                    'pandas>=1.5.0',
                    'pillow>=9.5.0',
                    'pyparsing>=3.0.9',
                    'python-dateutil>=2.8.2',
                    'pytz>=2023.3',
                    'scikit-image>=0.21.0',
                    'scipy>=1.10.0',
                    'six>=1.16.0',
                    'tifffile'],
    python_requires='>=3.8',
)
