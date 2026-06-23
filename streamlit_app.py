import importlib.util
import os
import sys
from pathlib import Path

import streamlit as st


APP_DIR = Path(__file__).parent / "Main App"
MAIN_FILE = APP_DIR / "main.py"


def run_main_app():
    if not MAIN_FILE.exists():
        st.error("Main App/main.py could not be found. Check the repository structure.")
        st.stop()

    if str(APP_DIR) not in sys.path:
        sys.path.insert(0, str(APP_DIR))

    os.chdir(APP_DIR)

    spec = importlib.util.spec_from_file_location("ai_gym_streamlit_main", MAIN_FILE)

    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load Main App/main.py.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "main"):
        raise RuntimeError("Main App/main.py must expose a main() function.")

    module.main()


run_main_app()
