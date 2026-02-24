import json
from utils import Colors


def highlight_line(line, matches_map):
    """Use ANSI Color code to highlight matched text in the line."""
    if not matches_map:
        return line.rstrip('\n')

    result = []
    i = 0
    line_len = len(line)
    # sorted_positions = sorted(matches_map.keys())
    
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
    """Formatted summary output as plain text with pattern names and matches."""
    output_lines = []
    for pattern_name, matches in results.items():
        if matches:
            output_lines.append(f"---{pattern_name}---")
            for match in matches:
                output_lines.append(match)
    return "\n".join(output_lines)


def format_json_output(results, unique=False):
    """Formatted JSON output of matched results."""
    if unique:
        output = {name: list(dict.fromkeys(matches)) for name, matches in results.items()}
    else:
        output = results
    return json.dumps(output, ensure_ascii=False, indent=2)
