import os
import sys
from path import Path

root = Path(__file__).abspath().parent
jupyter_notebook = Path(sys.executable) / '../Scripts/jupyter-notebook.exe'
notebook_root = root / 'examples/notebooks'
cmd = '{} --notebook-dir={}'.format(jupyter_notebook, notebook_root)

if __name__ == '__main__':
    os.system(cmd)
