import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build():
    """Nettoie les dossiers de build précédents"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

def create_executable():
    """Crée l'exécutable avec PyInstaller"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/i18n/locale', 'i18n/locale'),
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=['customtkinter', 'questionary'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='systemd-manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open('systemd-manager.spec', 'w') as f:
        f.write(spec_content)

    subprocess.run(['pyinstaller', 'systemd-manager.spec'], check=True)

def create_release_package():
    """Crée le package de release"""
    dist_dir = Path('dist')
    release_dir = Path('release')
    
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()

    # Copie l'exécutable
    shutil.copy(dist_dir / 'systemd-manager', release_dir)
    
    # Crée le script d'installation
    install_script = '''#!/bin/bash

# Vérification des droits sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Ce script doit être exécuté avec les droits sudo"
    exit 1
fi

# Copie de l'exécutable
cp systemd-manager /usr/local/bin/
chmod +x /usr/local/bin/systemd-manager

echo "Installation terminée !"
echo "Vous pouvez maintenant lancer systemd-manager depuis n'importe quel terminal"
'''
    
    with open(release_dir / 'install.sh', 'w') as f:
        f.write(install_script)
    
    # Rend le script d'installation exécutable
    os.chmod(release_dir / 'install.sh', 0o755)
    
    # Crée l'archive
    shutil.make_archive('systemd-manager-linux', 'tar', 'release')

if __name__ == '__main__':
    clean_build()
    create_executable()
    create_release_package() 