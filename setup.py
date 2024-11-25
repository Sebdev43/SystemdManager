from setuptools import setup, find_packages

setup(
    name="systemd-manager",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6",
        "questionary",
        "pyinstaller"
    ],
    author="Votre Nom",
    author_email="votre.email@example.com",
    description="Un gestionnaire de services systemd avec interface CLI et GUI",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/votre-username/systemd-manager",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
    ],
    entry_points={
        "console_scripts": [
            "systemd-manager=src.main:main",
        ],
    },
) 