#!/usr/bin/env python3
import sys
import argparse
import json
from pathlib import Path
from collections import OrderedDict

# 依赖检查
try:
    import regex
except ImportError:
    print("错误：需要 regex 库。请安装：pip install regex", file=sys.stderr)
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("错误：需要 PyYAML 库。请安装：pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# --- ✅ 修复：版本兼容性检查 ---
REGEX_SUPPORTS_TIMEOUT = False
try:
    # timeout 参数应该传给匹配函数，不是 compile()
    regex.search("test", "test", timeout=0.1)
    REGEX_SUPPORTS_TIMEOUT = True
except (TypeError, ValueError) as e:
    print("⚠️  警告：当前 regex 库不支持 timeout 参数，ReDoS 防护将失效。", file=sys.stderr)
    print("   建议升级：pip install --upgrade regex", file=sys.stderr)

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

# --- 数据结构 ---
class PatternInfo:
    def __init__(self, name, compiled_regex, color_index=0):
        self.name = name
        self.regex = compiled_regex
        self.color = Colors.HIGHLIGHTS[color_index % len(Colors.HIGHLIGHTS)]

# --- 功能函数 ---

def load_config():
    config_path = None
    if SYSTEM_CONFIG_PATH.exists():
        config_path = SYSTEM_CONFIG_PATH
    elif LOCAL_CONFIG_PATH.exists():
        config_path = LOCAL_CONFIG_PATH
    
    if not config_path:
        return None

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"错误：无法解析配置文件 {config_path}: {e}", file=sys.stderr)
        sys.exit(2)

def compile_patterns_from_config(config, pattern_names, timeout):
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

def highlight_line(line, matches_map):
    if not matches_map:
        return line.rstrip('\n')

    result = []
    i = 0
    line_len = len(line)
    sorted_positions = sorted(matches_map.keys())
    
    while i < line_len:
        if i in matches_map:
            end_pos, color = matches_map[i]
            result.append(color)
            result.append(line[i:end_pos])
            result.append(Colors.RESET)
            i = end_pos
        else:
            result.append(line[i])
            i += 1
            
    return "".join(result).rstrip('\n')

def format_summary_output(results):
    output_lines = []
    for pattern_name, matches in results.items():
        if matches:
            output_lines.append(f"---{pattern_name}---")
            for match in matches:
                output_lines.append(match)
    return "\n".join(output_lines)

def format_json_output(results, unique=False):
    if unique:
        output = {name: list(dict.fromkeys(matches)) for name, matches in results.items()}
    else:
        output = results
    return json.dumps(output, ensure_ascii=False, indent=2)

def process_input(file_obj, patterns, timeout, output_format, do_unique, do_highlight, exit_on_match):
    """处理输入流"""
    results = OrderedDict((pat.name, []) for pat in patterns)
    
    if output_format == 'json':
        do_highlight = False
    
    try:
        for line in file_obj:
            highlight_map = {}
            line_has_match = False
            
            for pat in patterns:
                try:
                    # ✅ timeout 传给 finditer()，不是 compile()
                    if REGEX_SUPPORTS_TIMEOUT:
                        matches = pat.regex.finditer(line, timeout=timeout)
                    else:
                        matches = pat.regex.finditer(line)
                    
                    for match in matches:
                        matched_text = match.group(0)
                        line_has_match = True
                        
                        if do_unique:
                            if matched_text not in results[pat.name]:
                                results[pat.name].append(matched_text)
                        else:
                            results[pat.name].append(matched_text)
                        
                        # 🔥 exit-on-match 逻辑
                        if exit_on_match:
                            if do_highlight:
                                start, end = match.span()
                                print(highlight_line(line, {start: (end, pat.color)}), flush=True)
                            elif output_format == 'summary':
                                print(f"[{pat.name}] {matched_text}", flush=True)
                            sys.exit(1)
                        
                        if do_highlight:
                            start, end = match.span()
                            if start not in highlight_map:
                                highlight_map[start] = (end, pat.color)
                                
                except Exception as e:
                    # ✅ 用字符串判断超时，避免直接引用 TimeoutError
                    if "timeout" in str(e).lower():
                        print(f"警告：模式 '{pat.name}' 匹配超时，跳过该行。", file=sys.stderr)
                        continue
                    else:
                        raise
            
            if do_highlight and line_has_match and not exit_on_match:
                print(highlight_line(line, highlight_map), flush=True)
                
    except KeyboardInterrupt:
        print("\n中断退出。", file=sys.stderr)
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as e:
        print(f"运行时错误：{e}", file=sys.stderr)
        sys.exit(2)
    
    return results

def main():
    Colors.disable()

    parser = argparse.ArgumentParser(
        description='安全正则匹配工具 (支持 ReDoS 防护、高亮、结构化输出、CI/CD 集成)'
    )
    parser.add_argument('file', nargs='?', type=argparse.FileType('r', encoding='utf-8'), 
                        default=sys.stdin, help='输入文件，默认为标准输入')
    parser.add_argument('--pattern', '-p', default='',
                        help='配置文件中的模式名称，多个用逗号分隔')
    parser.add_argument('--custom', '-c', action='append', default=[],
                        help='自定义正则，格式 name:regex (可多次使用)')
    parser.add_argument('--highlight', '-H', action='store_true',
                        help='高亮显示匹配内容（输出整行，仅适用于 summary 输出）')
    parser.add_argument('--output', '-o', choices=['summary', 'json'], 
                        default='summary',
                        help='输出格式：summary(默认), json')
    parser.add_argument('--unique', '-u', action='store_true',
                        help='去重输出（每个匹配值只出现一次）')
    parser.add_argument('--stat', '-s', action='store_true',
                        help='在结束时输出统计信息（仅 summary 模式）')
    parser.add_argument('--exit-on-match', '-e', action='store_true',
                        help='匹配到任意结果时立即以状态码 1 退出（用于 CI/CD 门禁）')
    parser.add_argument('--timeout', '-t', type=float, default=DEFAULT_TIMEOUT,
                        help=f'匹配超时时间（秒），默认 {DEFAULT_TIMEOUT}')
    
    args = parser.parse_args()

    # 参数冲突检查
    if args.output == 'json' and args.highlight:
        print("提示：--highlight 仅支持 summary 输出格式，已自动禁用。", file=sys.stderr)
        args.highlight = False
    
    if args.exit_on_match and args.stat:
        print("提示：--exit-on-match 与 --stat 互斥，已自动禁用 --stat。", file=sys.stderr)
        args.stat = False

    # 1. 加载配置
    config = load_config()
    
    # 2. 收集所有模式
    all_patterns = []
    
    if args.pattern:
        if not config:
            print("错误：使用了 --pattern 但未找到配置文件。", file=sys.stderr)
            sys.exit(2)
        pattern_names = [name.strip() for name in args.pattern.split(',') if name.strip()]
        all_patterns.extend(compile_patterns_from_config(config, pattern_names, args.timeout))
    
    if args.custom:
        all_patterns.extend(compile_custom_patterns(args.custom, args.timeout))
        
    if not all_patterns:
        print("错误：未指定任何匹配模式 (使用 --pattern 或 --custom)", file=sys.stderr)
        sys.exit(2)

    # 3. 处理输入并收集结果
    results = process_input(
        args.file, 
        all_patterns, 
        args.timeout, 
        args.output, 
        args.unique, 
        args.highlight,
        args.exit_on_match
    )

    # 4. 格式化并输出结果
    if args.output == 'summary':
        output_text = format_summary_output(results)
        if output_text:
            print(output_text)
        
        if args.stat:
            print("\n--- 匹配统计 ---", file=sys.stderr)
            for name, matches in results.items():
                if matches:
                    print(f"{name}: {len(matches)}", file=sys.stderr)
                    
    elif args.output == 'json':
        print(format_json_output(results, args.unique))
        

    sys.exit(0)

if __name__ == '__main__':
    main()