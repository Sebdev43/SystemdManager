from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="systemd-manager",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.6.1",
        "questionary>=2.0.1",
        "pyinstaller>=6.3.0",
        "customtkinter>=5.2.2",
        "python-i18n>=0.3.9",
        "psutil>=5.9.8",
        "typing-extensions>=4.9.0"
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.3',
            'pytest-cov>=4.1.0',
            'pytest-mock>=3.12.0',
            'black>=24.1.1',
            'flake8>=7.0.0',
            'mypy>=1.8.0',
        ],
    },
    python_requires='>=3.10',
    author="Votre Nom",
    author_email="votre.email@example.com",
    description="Un gestionnaire de services systemd avec interface CLI et GUI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/votre-username/systemd-manager",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications :: Qt",
        "Topic :: System :: Systems Administration",
    ],
    entry_points={
        "console_scripts": [
            "systemd-manager=src.main:main",
        ],
    },
    package_data={
        'systemd_manager': [
            'i18n/locale/*/*.po',
            'i18n/locale/*/*.mo',
        ],
    },
    include_package_data=True,
) 