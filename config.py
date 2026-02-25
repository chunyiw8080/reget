import sys
import yaml
from pathlib import Path
from utils import SYSTEM_CONFIG_PATH


def get_base_path():
    """Get the base path for config files, handling both normal and PyInstaller environments."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def get_embedded_default_config_path():
    """Get the path to the embedded default config file (for PyInstaller)."""
    return get_base_path() / "default.yaml"


def load_config():
    """
    Load configuration files
    Priority:
    1. System configuration
    2. Current working directory config.yaml
    3. Packaged built-in default.yaml
    """

    # System config
    if SYSTEM_CONFIG_PATH.exists():
        config_path = SYSTEM_CONFIG_PATH

    # local config in current directory
    elif Path("default.yaml").exists():
        config_path = Path("default.yaml")

    # Built-in default config (for PyInstaller)
    else:
        embedded = get_embedded_default_config_path()
        if embedded.exists():
            config_path = embedded
        else:
            return None

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error: Failed to parse config file {config_path}: {e}", file=sys.stderr)
        sys.exit(2)
