"""配置加载和管理"""
import sys
from pathlib import Path
from utils import SYSTEM_CONFIG_PATH

try:
    import yaml
except ImportError:
    print("错误：需要 PyYAML 库。请安装：pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def get_base_path():
    """获取程序运行基准路径（兼容 PyInstaller）"""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def get_embedded_default_config_path():
    """获取打包进二进制的 default.yaml 路径"""
    return get_base_path() / "default.yaml"


def load_config():
    """
    加载配置文件
    优先级：
    1. 系统配置
    2. 当前工作目录 config.yaml
    3. 打包内置 default.yaml
    """

    # 1️⃣ 系统级配置
    if SYSTEM_CONFIG_PATH.exists():
        config_path = SYSTEM_CONFIG_PATH

    # 2️⃣ 当前工作目录 config.yaml（用户可自定义）
    elif Path("config.yaml").exists():
        config_path = Path("config.yaml")

    # 3️⃣ 内置默认配置（PyInstaller 打包资源）
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
        print(f"错误：无法解析配置文件 {config_path}: {e}", file=sys.stderr)
        sys.exit(2)
