# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""


import re
from setuptools import setup


version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('badocker/badocker.py').read(),
    re.M
    ).group(1)


with open("README.rst", "rb") as f:
    long_descr = f.read().decode("utf-8")


setup(
    name = "cmdline-badocker",
    packages = ["badocker"],
    install_requires=[
          'termcolor',
      ],
    entry_points = {
        "console_scripts": ['badocker = badocker.badocker:main']
        },
    version = version,
    description = "Python command line application for Docker in Badoo.",
    long_description = long_descr,
    author = "banuchka",
    author_email = "tyrchenok@gmail.com",
    url = "Not YeT!",
    )