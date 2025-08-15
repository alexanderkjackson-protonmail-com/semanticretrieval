#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_text_sizes.py — minimal PDF text-size lister + header-based section hints.

Usage:
  python pdf_text_sizes.py path/to/file.pdf
  # Grep all big headings (example: >= 14pt):
  python pdf_text_sizes.py file.pdf | awk '{if ($1+0 >= 14) print}'
"""
import sys
import argparse
from collections import Counter, defaultdict
from statistics import median
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTPage, LTTextBox, LTTextContainer, LTTextLine, LTChar
import pdb

def iter_lines_with_sizes(pdf_path):
    """
    Yields tuples: (page_number, line_index_on_page, line_text, line_size)
    line_size = median of LTChar font sizes in the line (float) or None if no chars.
    """
    for pageno, page_layout in enumerate(extract_pages(pdf_path), start=1):
        line_idx = 0
        if pageno > 20:
            return
        """
        LTPage test
        LTTextBox
        LTTextLine
        """
        for element in page_layout:
            if isinstance(element, LTTextBox):
                for line in element:
                    if isinstance(line, LTTextLine):
                        charsizes = [c.size for c in line if isinstance(c, LTChar)]
                        if not charsizes:
                            continue
                        # Median is more stable than max/min across mixed spans.
                        line_size = float(median(charsizes))
                        text = line.get_text().rstrip("\n")
                        # Skip empty/whitespace-only lines
                        if text.strip():
                            yield (pageno, line_idx, text, line_size)
                            line_idx += 1

def round_size(sz, step=0.5):
    """Round a font size to the nearest step (e.g., 0.5pt) for tidy grouping."""
    return round(sz / step) * step

def infer_body_and_headers(size_list):
    """
    Heuristic:
      - Group sizes by 0.5pt rounding; take the most frequent as body size.
      - Header sizes are groups strictly larger than body and occurring at least a few times
        OR clear outliers (> body + 2pt).
    Returns: body_size (float), header_sizes_sorted_desc (list of floats)
    """
    grouped = Counter(round_size(s) for s in size_list)
    if not grouped:
        return None, []
    # Body = modal size
    body_size = grouped.most_common(1)[0][0]

    # Candidates above body
    above = [(sz, cnt) for sz, cnt in grouped.items() if sz > body_size]
    # Heuristic threshold: anything >= body+2pt or with reasonable frequency
    header_candidates = [sz for sz, cnt in above if (sz >= body_size + 2.0) or (cnt >= max(2, len(size_list) * 0.01))]
    header_sizes = sorted(set(header_candidates), reverse=True)
    return body_size, header_sizes

def build_sections(lines, header_sizes):
    """
    Given stream of (page, idx, text, size) and a set/list of header sizes,
    start a new section when a line's rounded size matches a header size.
    Returns: sections = list of dicts:
      {
        'section_id': int,
        'start': (page, idx),
        'end':   (page, idx),   # exclusive end marker line position (last line in section has idx end-1 on that page)
        'header_text': str,
        'header_size': float,
        'lines': [(page, idx, text, size), ...]
      }
    """
    if not header_sizes:
        return []

    header_set = set(header_sizes)
    sections = []
    current = None

    def finalize_section(end_pos):
        if current is not None:
            current['end'] = end_pos
            sections.append(current)

    for (page, idx, text, size) in lines:
        is_header = round_size(size) in header_set
        if is_header:
            # Close previous section at this header's start
            finalize_section((page, idx))
            # Start new section
            current = {
                'section_id': len(sections) + 1,
                'start': (page, idx),
                'end': None,
                'header_text': text.strip(),
                'header_size': round_size(size),
                'lines': []
            }
        # Append line to current (if any); if none yet, we’re before the first header
        if current is None:
            # Create a preface section if content appears before first header
            current = {
                'section_id': 0,
                'start': (page, idx),
                'end': None,
                'header_text': '(preface)',
                'header_size': round_size(size),
                'lines': []
            }
        current['lines'].append((page, idx, text, size))

    # Close last section at EOF (end marker = one past last line)
    if current is not None:
        # Best-effort: end at the last seen line position + 1
        last_page, last_idx, _, _ = current['lines'][-1]
        finalize_section((last_page, last_idx + 1))

    return sections

def main():
    ap = argparse.ArgumentParser(description="Print per-line PDF text sizes (greppable) and section hints based on header sizes.")
    ap.add_argument("pdf", help="Path to the PDF")
    args = ap.parse_args()

    # 1) Extract lines with sizes
    raw_lines = list(iter_lines_with_sizes(args.pdf))

    if not raw_lines:
        # Nothing to print; keep behavior simple
        return

    # 2) Print greppable lines: "<size> <text>"
    #    NOTE: Keep this clean for grep/awk users.
    for (_page, _idx, text, size) in raw_lines:
        # Normalize internal whitespace to single space for consistent grepping
        norm = " ".join(text.split())
        print(f"{size:.2f} {norm}")

    # 3) Extra aids (go to stderr-like channel? Keeping minimal: print after a clear divider.)
    print("\n--- SIZE SUMMARY ---", file=sys.stderr)
    sizes = [s for *_rest, s in raw_lines]
    grouped = Counter(round_size(s) for s in sizes)
    for sz, cnt in sorted(grouped.items(), key=lambda x: (-x[1], -x[0])):
        print(f"{cnt:5d} lines @ {sz:.1f}pt", file=sys.stderr)

    # 4) Infer body size and header sizes
    body_size, header_sizes = infer_body_and_headers(sizes)
    print("\n--- LAYOUT GUESS ---", file=sys.stderr)
    if body_size is None:
        print("No text detected.", file=sys.stderr)
        return
    print(f"Body size guess: {body_size:.1f}pt", file=sys.stderr)
    if header_sizes:
        print("Header sizes (desc): " + ", ".join(f"{h:.1f}pt" for h in header_sizes), file=sys.stderr)
    else:
        print("No clear header sizes detected above body.", file=sys.stderr)

    # 5) Build a section map using header sizes
    if header_sizes:
        # Reuse the same lines sequence; we want rounded sizes for header match
        sections = build_sections(raw_lines, header_sizes)
        print("\n--- SECTION CANDIDATES (by header lines) ---", file=sys.stderr)
        for sec in sections:
            sid = sec['section_id']
            (sp, si) = sec['start']
            (ep, ei) = sec['end']
            hdr = " ".join(sec['header_text'].split())
            print(f"[Section {sid:02d}] start=page{sp}:line{si} end=page{ep}:line{ei}  header='{hdr}'  size={sec['header_size']:.1f}pt", file=sys.stderr)

            # Optional: show first few lines of each section to orient yourself
            preview = sec['lines'][:3]
            for (pp, ii, tx, sz) in preview:
                tnorm = " ".join(tx.split())
                print(f"    {sz:.2f} {tnorm}", file=sys.stderr)

if __name__ == "__main__":
    main()
