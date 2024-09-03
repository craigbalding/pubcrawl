from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="pubcrawl",
    version="0.1.0",
    author="Craig Balding",
    author_email="craig@threatprompt.com",
    description="A one-shot CLI tool to scrape a public URL that depends on JavaScript",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/craigbalding/pubcrawl",
    packages=find_packages(include=['pubcrawl', 'pubcrawl.*']),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'pubcrawl=pubcrawl.pubcrawl:main',
        ],
    },
)
