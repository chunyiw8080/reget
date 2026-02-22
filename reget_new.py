#!/usr/bin/env python3
"""
安全正则匹配工具 (支持 ReDoS 防护、高亮、结构化输出、CI/CD 集成)
"""
import sys
import argparse

from utils import Colors, check_regex_timeout_support, DEFAULT_TIMEOUT
from config import load_config
from patterns import compile_patterns_from_config, compile_custom_patterns
from output import format_summary_output, format_json_output
from processor import process_input


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
    # 如果存在hightlight参数，禁用格式化输出
    if args.output == 'summary' and not args.highlight:
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
