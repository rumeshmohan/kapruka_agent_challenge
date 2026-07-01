import sys
from pathlib import Path

root_path = str(Path(__file__).resolve().parent)
if root_path not in sys.path:
    sys.path.append(root_path)

import ui.app