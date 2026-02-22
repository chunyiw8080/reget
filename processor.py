"""核心处理逻辑：读取、匹配、收集结果"""
import sys
from collections import OrderedDict
from output import highlight_line

# 导入 regex 以支持 timeout
try:
    import regex
    REGEX_SUPPORTS_TIMEOUT = False
    try:
        regex.search("test", "test", timeout=0.1)
        REGEX_SUPPORTS_TIMEOUT = True
    except (TypeError, ValueError):
        REGEX_SUPPORTS_TIMEOUT = False
except ImportError:
    REGEX_SUPPORTS_TIMEOUT = False


def process_input(file_obj, patterns, timeout, output_format, do_unique, do_highlight, exit_on_match):
    """
    处理输入流，执行正则匹配并收集结果
    
    Args:
        file_obj: 输入文件对象
        patterns: PatternInfo 列表
        timeout: 匹配超时时间
        output_format: 输出格式 ('summary' 或 'json')
        do_unique: 是否去重
        do_highlight: 是否高亮显示
        exit_on_match: 匹配到结果时是否立即退出
    
    Returns:
        OrderedDict: {pattern_name: [matches]}
    """
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
