from pathlib import Path

import streamlit as st
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONF_DIR = PROJECT_ROOT / "conf"


@st.cache_data(show_spinner=False)
def load_config() -> dict:
    config: dict = {}
    example_path = CONF_DIR / "config.example.yaml"
    if example_path.exists():
        config.update(yaml.safe_load(example_path.read_text(encoding="utf-8")) or {})
    local_path = CONF_DIR / "config.yaml"
    if local_path.exists():
        config.update(yaml.safe_load(local_path.read_text(encoding="utf-8")) or {})
    return config