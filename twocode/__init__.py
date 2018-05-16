from .lang import Twocode
from .console import Console#, parse_args

__version__ = "0.5"

def main():
    console = Console()
    console.interact()
    return 0
