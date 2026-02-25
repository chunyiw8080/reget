import sys
import regex
from utils import Colors

class PatternInfo:
    def __init__(self, name, compiled_regex, color_index=0):
        self.name = name
        self.regex = compiled_regex
        self.color = Colors.HIGHLIGHTS[color_index % len(Colors.HIGHLIGHTS)]


def compile_patterns_from_config(config, pattern_names):
    """Compile regex patterns from config based on specified pattern names"""
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
                    compiled = regex.compile(regex_str)
                    patterns.append(PatternInfo(name, compiled, idx))
                except regex.error as e:
                    print(f"Error: Pattern '{name}' failed to compile: {e}", file=sys.stderr)
                    sys.exit(2)
        except KeyError:
            print(f"Error: Pattern '{name}' not found in config", file=sys.stderr)
            sys.exit(2)
    return patterns


def compile_custom_patterns(custom_args):
    """Complile custom regex pattern"""
    patterns = []
    for idx, item in enumerate(custom_args):
        if ':' not in item:
            print(f"Error: Custom pattern format should be 'name:regex', received: {item}", file=sys.stderr)
            sys.exit(2)
        name, regex_str = item.split(':', 1)
        try:
            compiled = regex.compile(regex_str)
            patterns.append(PatternInfo(f"custom_{name}", compiled, idx + 100))
        except regex.error as e:
            print(f"Error: Custom pattern '{name}' failed to compile: {e}", file=sys.stderr)
            sys.exit(2)
    return patterns
