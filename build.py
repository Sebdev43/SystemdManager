import PyInstaller.__main__
import sys
import os

def check_dependencies():
    required_files = [
        "src/main.py",
        "src/i18n/locale",
    ]
    for file in required_files:
        if not os.path.exists(file):
            raise FileNotFoundError(f"Le fichier ou répertoire requis est manquant : {file}")

def build_application():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    PyInstaller.__main__.run([
    'src/main.py',
    '--name=systemd-manager',
    '--onefile',
    '--clean',
    '--debug=all',
    '--add-data=src/i18n/locale:i18n/locale',
    '--hidden-import=pkg_resources.py2_warn',
    '--hidden-import=jaraco.text',
    '--hidden-import=setuptools',
    '--hidden-import=PyQt6.QtCore',
    '--hidden-import=PyQt6.QtGui',
    '--hidden-import=PyQt6.QtWidgets',
    '--hidden-import=customtkinter',
    '--hidden-import=questionary',
    '--hidden-import=ipaddress',
    '--hidden-import=pyimod02_importers',
    '--hidden-import=pyiboot01_bootstrap',
    '--hidden-import=prompt_toolkit',
    '--hidden-import=prompt_toolkit.key_binding.bindings.search',
    '--hidden-import=prompt_toolkit.input.vt100',
    '--hidden-import=prompt_toolkit.input.posix_utils',
    '--hidden-import=termios',
    '--hidden-import=tty',
    '--hidden-import=tkinter',
    '--add-binary=/usr/lib/x86_64-linux-gnu/libxcb-*:lib/',

    '--exclude-module=tkinter.test',
    '--exclude-module=unittest',
    '--noconsole',
    '--windowed',
    f'--workpath={os.path.join(root_dir, "build")}',
    f'--distpath={os.path.join(root_dir, "dist")}'
])


if __name__ == "__main__":
    try:
        print("🔨 Début de la compilation...")
        check_dependencies()
        build_application()
        print("✅ Compilation terminée avec succès!")
    except FileNotFoundError as fnfe:
        print(f"❌ Fichier manquant : {str(fnfe)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur lors de la compilation: {str(e)}")
        sys.exit(1)
