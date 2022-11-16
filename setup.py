import os
from glob import glob
from imp import load_source

from setuptools import find_packages, setup

__version__ = load_source(
    "pystac_client.version", "pystac_client/version.py"
).__version__

from os.path import basename, splitext

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md")) as readme_file:
    readme = readme_file.read()

setup(
    name="pystac-client",
    version=__version__,
    description=(
        "Python library for working with Spatiotemporal Asset Catalog (STAC)."
    ),
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Jon Duckworth, Matthew Hanson",
    author_email="duckontheweb@gmail.com, matt.a.hanson@gmail.com",
    url="https://github.com/stac-utils/pystac-client.git",
    packages=find_packages(exclude=("tests",)),
    py_modules=[splitext(basename(path))[0] for path in glob("pystac_client/*.py")],
    include_package_data=True,
    package_data={"pystac_client": ["py.typed"]},
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.27.1",
        "pystac>=1.4.0",
        "python-dateutil>=2.7.0",
    ],
    extras_require={"validation": ["jsonschema>=4.5.1"]},
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords=["pystac", "imagery", "raster", "catalog", "STAC"],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    test_suite="tests",
    entry_points={"console_scripts": ["stac-client=pystac_client.cli:cli"]},
)
