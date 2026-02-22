"""正则模式编译和管理"""
import sys
from utils import Colors

try:
    import regex
except ImportError:
    print("错误：需要 regex 库。请安装：pip install regex", file=sys.stderr)
    sys.exit(1)


class PatternInfo:
    """模式信息容器"""
    def __init__(self, name, compiled_regex, color_index=0):
        self.name = name
        self.regex = compiled_regex
        self.color = Colors.HIGHLIGHTS[color_index % len(Colors.HIGHLIGHTS)]


def compile_patterns_from_config(config, pattern_names, timeout):
    """从配置文件编译模式"""
    patterns = []
    if not config or 'pattern' not in config:
        return patterns
        
    for idx, name in enumerate(pattern_names):
        try:
            pattern_data = config['pattern'][name]
            regex_list = pattern_data.get('regex', [])
            if not isinstance(regex_list, list):
                regex_list = [regex_list]
            
            for regex_str in regex_list:
                try:
                    # ✅ compile() 不传 timeout
                    compiled = regex.compile(regex_str)
                    patterns.append(PatternInfo(name, compiled, idx))
                except regex.error as e:
                    print(f"错误：模式 '{name}' 编译失败：{e}", file=sys.stderr)
                    sys.exit(2)
        except KeyError:
            print(f"错误：配置文件中未找到模式 '{name}'", file=sys.stderr)
            sys.exit(2)
    return patterns


def compile_custom_patterns(custom_args, timeout):
    """编译自定义正则模式"""
    patterns = []
    for idx, item in enumerate(custom_args):
        if ':' not in item:
            print(f"错误：自定义模式格式应为 'name:regex'，收到：{item}", file=sys.stderr)
            sys.exit(2)
        name, regex_str = item.split(':', 1)
        try:
            # ✅ compile() 不传 timeout
            compiled = regex.compile(regex_str)
            patterns.append(PatternInfo(f"custom_{name}", compiled, idx + 100))
        except regex.error as e:
            print(f"错误：自定义模式 '{name}' 编译失败：{e}", file=sys.stderr)
            sys.exit(2)
    return patterns
