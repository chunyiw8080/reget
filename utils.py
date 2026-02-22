"""工具函数和常量定义"""
import sys
from pathlib import Path

# --- 常量与配置 ---
SYSTEM_CONFIG_PATH = Path('/etc/reget/reget.yaml')
LOCAL_CONFIG_PATH = Path('./reget.yaml')
DEFAULT_TIMEOUT = 0.5

# ANSI 颜色代码
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
    """检查 regex 库是否支持 timeout 参数"""
    try:
        import regex
    except ImportError:
        return False
    
    try:
        regex.search("test", "test", timeout=0.1)
        return True
    except (TypeError, ValueError):
        print("⚠️  警告：当前 regex 库不支持 timeout 参数，ReDoS 防护将失效。", file=sys.stderr)
        print("   建议升级：pip install --upgrade regex", file=sys.stderr)
        return False
