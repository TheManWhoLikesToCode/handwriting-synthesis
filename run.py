#!/usr/bin/env python
"""
Handwriting SVG Generator - Generate handwritten text as SVG files.

Usage:
    python run.py "Your text here"
    python run.py --file input.txt
    python run.py --file input.txt --output my_output.svg --style 5 --bias 0.8
    python run.py  # Interactive mode
"""

import argparse
import sys
import textwrap
from demo import Hand
from drawing import alphabet

# Valid characters the model can render
VALID_CHARS = set(alphabet)


def validate_text(text):
    """Check for invalid characters and return cleaned text with warnings."""
    invalid_chars = set()
    cleaned = []
    
    for char in text:
        if char in VALID_CHARS:
            cleaned.append(char)
        elif char == '\n':
            # Newlines are handled by line splitting
            cleaned.append(char)
        elif char == '\t':
            # Convert tabs to spaces
            cleaned.append(' ')
        else:
            invalid_chars.add(char)
            # Try common substitutions
            if char in '""':
                cleaned.append('"')
            elif char in '\'\u2018\u2019`':
                cleaned.append("'")
            elif char in '–—':
                cleaned.append('-')
            elif char in '…':
                cleaned.append('...')
            else:
                # Skip unknown characters
                pass
    
    if invalid_chars:
        print(f"Warning: Removed unsupported characters: {invalid_chars}")
    
    return ''.join(cleaned)


def estimate_text_width(text, scale_factor=1.5, avg_char_width=10):
    """
    Estimate the rendered width of text in SVG units.
    
    Args:
        text: The text string to measure
        scale_factor: The stroke scaling factor used in rendering (default: 1.5)
        avg_char_width: Average character width in stroke units (default: 10)
    
    Returns:
        Estimated width in SVG units
    """
    # Empirically determined: average character renders to ~10 units before scaling
    # After 1.5x scaling, that's ~15 units per character
    return len(text) * avg_char_width * scale_factor


def wrap_text_to_width(text, available_width, scale_factor=1.5, avg_char_width=10):
    """
    Wrap text into lines that fit within a pixel/unit width.
    
    Args:
        text: The text to wrap
        available_width: Maximum width in SVG units
        scale_factor: Stroke scaling factor (default: 1.5)
        avg_char_width: Average character width estimate (default: 10)
    
    Returns:
        List of lines that should fit within the available width
    """
    # Calculate max characters that fit in available width
    char_width = avg_char_width * scale_factor
    max_chars = max(1, int(available_width / char_width))
    
    # Ensure we don't exceed the hard limit of 75 chars (model constraint)
    max_chars = min(max_chars, 75)
    
    return wrap_text(text, max_chars=max_chars)


def wrap_text(text, max_chars=75):
    """Wrap text into lines that fit within max_chars limit."""
    # Ensure max_chars doesn't exceed model limit
    max_chars = min(max_chars, 75)
    
    # Split by existing newlines first
    paragraphs = text.split('\n')
    lines = []
    
    for para in paragraphs:
        if not para.strip():
            lines.append('')  # Preserve blank lines as empty string (will be skipped in rendering)
        else:
            # Wrap each paragraph
            wrapped = textwrap.wrap(para, width=max_chars, break_long_words=True)
            lines.extend(wrapped if wrapped else [''])
    
    return lines


def interactive_mode():
    """Run interactive prompt for text input."""
    print("\n" + "="*60)
    print("  HANDWRITING SVG GENERATOR")
    print("="*60)
    print("\nEnter your text below. Press Enter twice to generate.\n")
    
    lines = []
    empty_count = 0
    
    while True:
        try:
            line = input()
            if line == '':
                empty_count += 1
                if empty_count >= 2:
                    break
                lines.append('')
            else:
                empty_count = 0
                lines.append(line)
        except EOFError:
            break
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Generate handwritten text as SVG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py "Hello World"
  python run.py "Dear Mom, I love you!" -s 7 -b 0.9
  python run.py --file letter.txt --output letter.svg
  python run.py  # Interactive mode
  
Styles 0-12 offer different handwriting personalities.
Bias 0.5-2.0 controls consistency (higher = neater writing).
        """
    )
    parser.add_argument(
        'text', 
        nargs='?', 
        help='Text to write'
    )
    parser.add_argument(
        '--file', '-f',
        help='Read text from a file'
    )
    parser.add_argument(
        '--output', '-o',
        default='img/output.svg',
        help='Output SVG filename (default: img/output.svg)'
    )
    parser.add_argument(
        '--style', '-s',
        type=int,
        default=3,
        choices=range(0, 13),
        metavar='0-12',
        help='Handwriting style 0-12 (default: 3)'
    )
    parser.add_argument(
        '--bias', '-b',
        type=float,
        default=0.75,
        help='Sampling bias 0.5-2.0, higher=neater (default: 0.75)'
    )
    parser.add_argument(
        '--color', '-c',
        default='#000033',
        help='Stroke color (default: #000033 dark blue)'
    )
    parser.add_argument(
        '--width', '-w',
        type=float,
        default=1.2,
        help='Stroke width (default: 1.2)'
    )
    parser.add_argument(
        '--max-chars', '-m',
        type=int,
        default=75,
        help='Maximum characters per line for wrapping (default: 75)'
    )
    parser.add_argument(
        '--left-margin',
        type=int,
        default=50,
        help='Left margin in SVG units (default: 50)'
    )
    parser.add_argument(
        '--right-margin',
        type=int,
        default=50,
        help='Right margin in SVG units (default: 50)'
    )
    parser.add_argument(
        '--line-height',
        type=int,
        default=60,
        help='Line height in SVG units (default: 60)'
    )
    parser.add_argument(
        '--view-width',
        type=int,
        default=1000,
        help='Total SVG width in units (default: 1000)'
    )
    parser.add_argument(
        '--list-styles',
        action='store_true',
        help='Show available styles and exit'
    )
    
    args = parser.parse_args()
    
    # List styles mode
    if args.list_styles:
        print("\nAvailable Handwriting Styles:")
        print("-" * 40)
        for i in range(13):
            print(f"  Style {i:2d}")
        print("\nTip: Try different styles to find one you like!")
        print("Example: python run.py 'Test' --style 7")
        sys.exit(0)
    
    # Get the text to write
    if args.file:
        try:
            with open(args.file, 'r') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
    elif args.text:
        text = args.text
    else:
        # Interactive mode
        text = interactive_mode()
    
    if not text.strip():
        print("Error: No text provided")
        sys.exit(1)
    
    # Validate and clean text
    text = validate_text(text)
    
    # Calculate available width for text (respecting margins)
    available_width = args.view_width - args.left_margin - args.right_margin
    
    # Wrap text into lines based on available width (coordinate-aware)
    # If user explicitly set max_chars, respect that; otherwise use width-based wrapping
    if args.max_chars != 75:  # User explicitly set max_chars
        lines = wrap_text(text, args.max_chars)
    else:
        # Use coordinate-based wrapping based on available width
        lines = wrap_text_to_width(text, available_width)
    
    if not lines:
        print("Error: No valid text to render")
        sys.exit(1)
    
    # Calculate final SVG height
    svg_height = args.line_height * (len(lines) + 1)
    
    print(f"\nGenerating handwriting...")
    print(f"  Lines: {len(lines)}")
    print(f"  Style: {args.style}")
    print(f"  Bias:  {args.bias}")
    print(f"  Color: {args.color}")
    print(f"  SVG Size: {args.view_width} x {svg_height}")
    print(f"  Margins: L={args.left_margin}, R={args.right_margin}")
    
    # Initialize the Hand model
    hand = Hand()
    
    # Create per-line parameters (same value for all lines)
    biases = [args.bias] * len(lines)
    styles = [args.style] * len(lines)
    stroke_colors = [args.color] * len(lines)
    stroke_widths = [args.width] * len(lines)
    
    # Generate the SVG
    hand.write(
        filename=args.output,
        lines=lines,
        biases=biases,
        styles=styles,
        stroke_colors=stroke_colors,
        stroke_widths=stroke_widths,
        left_margin=args.left_margin,
        right_margin=args.right_margin,
        line_height=args.line_height,
        view_width=args.view_width
    )
    
    print(f"\n✓ Generated: {args.output}")


if __name__ == '__main__':
    main()