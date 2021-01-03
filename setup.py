import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="head-scroll",
    version="0.1.0",
    author="James Stout",
    author_email="james.wolf.stout@gmail.com",
    description="Library for scrolling using head gestures",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wolfmanstout/head-scroll",
    packages=["head_scroll"],
    install_requires=[
    ],
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
