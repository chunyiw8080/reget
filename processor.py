import sys
from collections import OrderedDict
from output import highlight_line

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
    Process the input stream, perform Regex matching, and collect the results.
    
    Args:
        file_obj: file object
        patterns: Pattern list defined in user config or in the built-in patterns
        timeout: match timeout in seconds
        output_format: output format, summary or json
        do_unique: Remove duplicates
        do_highlight: Show highlighted text
        exit_on_match: non-zero exit immediately when a match is found
    
    Returns:
        OrderedDict: {pattern_name: [matches]}
    """
    results = OrderedDict((pat.name, []) for pat in patterns)
    
    if output_format == 'json':
        do_highlight = False
    
    try:
        for line in file_obj:
            highlight_map = {}
            # line_has_match = False
            
            for pattern in patterns:
                try:
                    if REGEX_SUPPORTS_TIMEOUT:
                        matches = pattern.regex.finditer(line, timeout=timeout)
                    else:
                        matches = pattern.regex.finditer(line)
                    
                    for match in matches:
                        matched_text = match.group(0)
                        # line_has_match = True
                        
                        if do_unique:
                            if matched_text not in results[pattern.name]:
                                results[pattern.name].append(matched_text)
                        else:
                            results[pattern.name].append(matched_text)
                        
                        # exit-on-match
                        if exit_on_match:
                            if do_highlight:
                                start, end = match.span()
                                print(highlight_line(line, {start: (end, pattern.color)}), flush=True)
                            elif output_format == 'summary':
                                print(f"[{pattern.name}] {matched_text}", flush=True)
                            sys.exit(1)
                        
                        if do_highlight:
                            start, end = match.span()
                            if start not in highlight_map:
                                highlight_map[start] = (end, pattern.color)
                                
                except Exception as e:
                    # Use keywords to determine timeouts, and avoid directly referencing TimeoutError.
                    if "timeout" in str(e).lower():
                        print(f"Warning: Pattern '{pattern.name}' matching timed out, skipping line.", file=sys.stderr)
                        continue
                    else:
                        raise
            
            if do_highlight and not exit_on_match:
                # Always output the whole text line when highlight is enabled
                # Return the original line content if no matches
                print(highlight_line(line, highlight_map), flush=True)
                
    except KeyboardInterrupt:
        print("\nKeyboard Interrupted", file=sys.stderr)
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    
    return results
