import sys
import os
from pathlib import Path

DEFAULT_TIMEOUT = 0.5

def get_config_path():
    if sys.platform.startswith('win'):
        return Path('./reget.yaml')
    else:
        return Path('/etc/reget/reget.yaml')

# ANSI Color codes for highlighting
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    HIGHLIGHTS = [
        '\033[91m', '\033[92m', '\033[93m', 
        '\033[94m', '\033[95m', '\033[96m',
    ]
    
    @staticmethod
    def disable():
        if not sys.stdout.isatty():
            Colors.HIGHLIGHTS = ['']
            Colors.RESET = ''

def check_regex_timeout_support():
    """Check if installed regex version supports timeout parameter."""
    try:
        import regex
    except ImportError:
        return False

def mmap_lines(path, encoding='utf-8'):
    """
    Open the file using mmap and return the text line by line (preserving newlines).
    This function falls back to normal line-by-line reading if mmap is unavailable or fails.
    Returns a generator that produces the decoded string (including newline characters).
    """
    import mmap as _mmap
    
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path) # raise error when file not found
    
    size = os.path.getsize(path)
    if size == 0:
        return # return when file is empty

    with p.open('rb') as f:
        try:
            mm = _mmap.mmap(f.fileno(), 0, access=_mmap.ACCESS_READ)
        except (ValueError, OSError):
            f.seek(0)
            for raw in f:
                yield raw.decode(encoding, errors='replace')
            return

        try:
            start = 0
            size = len(mm)
            while start < size:
                nl = mm.find(b"\n", start)
                if nl == -1:
                    chunk = mm[start: size]
                    if chunk:
                        yield chunk.decode(encoding, errors='replace')
                    break
                chunk = mm[start: nl + 1]
                yield chunk.decode(encoding, errors='replace')
                start = nl + 1
        finally:
            mm.close()

def list_patterns(config=None):
    """
    List all patterns definded in the config file or defalt config file.
    """
    patterns = config.get('pattern', {})
    if not patterns:
        return ""
    result = []
    for key, value in patterns.items():
        desc = value.get('description', '')
        if desc:
            result.append(f"{key}: {desc}")
        else:
            result.append(f"{key}: -")
    return "\n".join(result)