import os
import twocode

codebase = os.path.join(os.path.dirname(os.path.dirname(twocode.__file__)), "code")
if not os.path.exists(os.path.join(codebase, "__package__.2c")):
    codebase = os.path.dirname(__file__)
    if not os.path.exists(os.path.join(codebase, "__package__.2c")):
        raise Exception("Twocode codebase not found")
