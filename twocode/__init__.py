from .lang import Twocode
from .console import Console#, parse_args
import sys

__version__ = "0.5"
url = "https://github.com/MrCoft/twocode"

def main():
    console = Console()
    print("Twocode {} - {}".format(__version__, url), file=sys.stderr, flush=True)
    console.interact()
    return 0
