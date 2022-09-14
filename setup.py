
from cx_Freeze import setup, Executable

import sys
base = 'Win32GUI' if sys.platform=='win32' else None
includefiles = ['assets']
executables = [
    Executable('SlappyBird.py', base=base, target_name = 'SlappyBird')
]

setup(name='Slappy Bird',
      version = '1',
      options = {'build_exe': {'include_files':includefiles}},
      executables = executables)