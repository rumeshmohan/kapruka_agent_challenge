import sys
import os
from pathlib import Path

# Force correct port for HF Spaces
os.environ['STREAMLIT_SERVER_PORT'] = '7860'
os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

root_path = str(Path(__file__).resolve().parent)
if root_path not in sys.path:
    sys.path.append(root_path)

import ui.app