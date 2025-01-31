from pathlib import Path
import subprocess
import hashlib
import shutil
import json
import sys
import os

class RytonInstaller:
    def __init__(self):
        self.paths = {
            'system': Path('/usr/local/lib/ryton'),
            'user': Path.home() / '.local/lib/ryton',
            'bin_system': Path('/usr/local/bin'), 
            'bin_user': Path.home() / '.local/bin'
        }

    def install(self, install_type='user'):
        print(f"Starting Ryton installation ({install_type})...")
        
        lib_path = self.paths[install_type]
        bin_path = self.paths[f'bin_{install_type}']

        try:
            # Копируем три компонента отдельно
            shutil.copytree('ryton', lib_path / 'ryton')
            shutil.copytree('rytonpm', lib_path / 'rytonpm')
            shutil.copytree('rytonbuilder', lib_path / 'rytonbuilder')
            
            # Создаем симлинки на бинарники
            bin_path.mkdir(parents=True, exist_ok=True)
            for tool in ['ryton', 'rytonpm', 'rytonbuilder']:
                link = bin_path / tool
                if link.exists():
                    link.unlink()
                link.symlink_to(lib_path / tool / f'{tool}.bin')

            print(f"Ryton installed to {lib_path}")
            return True

        except Exception as e:
            print(f"Installation failed: {e}")
            return False

    def get_install_paths(self, install_type):
        return {
            'lib': self.paths[install_type],
            'bin': self.paths[f'bin_{install_type}']
        }

    def check_system(self):
        # Проверка системных требований
        required_libs = ['libpython3.so', 'libstdc++.so']
        
        for lib in required_libs:
            if not self.find_library(lib):
                raise RuntimeError(f"Required library {lib} not found")
                
        # Проверка свободного места
        if shutil.disk_usage('/').free < 100_000_000:  # 100MB
            raise RuntimeError("Not enough disk space")

    def find_library(self, name):
        try:
            result = subprocess.run(
                ['ldconfig', '-p'], 
                capture_output=True, 
                text=True
            )
            return name in result.stdout
        except:
            return False

    def backup_existing(self, install_path):
        if install_path.exists():
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            self.backup_path = install_path.parent / f'ryton_backup_{timestamp}'
            shutil.move(install_path, self.backup_path)

    def verify_installation(self, install_path):
        # Проверка бинарников
        for binary in self.binaries:
            bin_path = install_path / f'{binary}.bin'
            if not bin_path.exists() or not os.access(bin_path, os.X_OK):
                return False
                
        # Проверка стандартной библиотеки
        if not (install_path / 'std').exists():
            return False
            
        return True

    def create_symlinks(self, bin_path, lib_path):
        bin_path.mkdir(parents=True, exist_ok=True)
        
        for binary in self.binaries:
            link = bin_path / binary
            target = lib_path / f'{binary}.bin'
            
            if link.exists():
                link.unlink()
            link.symlink_to(target)

    def rollback(self, install_path):
        try:
            shutil.rmtree(install_path)
            if self.backup_path and self.backup_path.exists():
                shutil.move(self.backup_path, install_path)
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description='Ryton Installer')
    parser.add_argument('--type', choices=['system', 'user'],
                       default='user', help='Installation type')
    args = parser.parse_args()

    installer = RytonInstaller()
    success = installer.install(args.type)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
