import sys
import yaml
from pathlib import Path
from utils import get_config_path

SYSTEM_CONFIG_PATH = get_config_path()

def get_base_path():
    """Get the base path for config files, handling both normal and PyInstaller environments."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def get_embedded_default_config_path():
    """Get the path to the embedded default config file (for PyInstaller)."""
    return get_base_path() / "reget.yaml"


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

def init_config():
    path = get_config_path()
    if path.exists():
        print(f"Error: Config file already exists at {path}", file=sys.stderr)
        sys.exit(1)
    else:
        try:
            embedded = get_embedded_default_config_path()
            if embedded.exists():
                with embedded.open('r', encoding='utf-8') as src, path.open('w', encoding='utf-8') as dst:
                    dst.write(src.read())
                print(f"Config file initialized at {path}")
            else:
                print("Error: Embedded default config not found. Cannot initialize config file.", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"Error: Failed to initialize config file: {e}", file=sys.stderr)
            sys.exit(1)
