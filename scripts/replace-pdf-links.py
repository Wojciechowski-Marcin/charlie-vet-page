#!/usr/bin/env python3
"""
Script to:
1. Split podsumowanie-weterynaryjne.md by headers
2. Anonymize content
3. Replace PDF links with Google Drive links
4. Generate multiple docs/ files with Jekyll front matter
"""

import json
import re
from pathlib import Path

# Page configuration - title and navigation order
PAGE_CONFIG = {
    "index.md": {"title": "Strona Główna", "nav_order": 1},
    "current-state.md": {"title": "Aktualny Stan", "nav_order": 2},
    "visits.md": {"title": "Historia Wizyt", "nav_order": 3},
    "lab-results.md": {"title": "Wyniki Badań", "nav_order": 4},
    "files.md": {"title": "Dokumenty", "nav_order": 5},
}

# Map section headers to output files
# Sections are processed in order - first matching header wins for a section
# Note: Only ## headers are used for splitting. ### headers stay with their parent.
SECTION_MAPPING = [
    # index.md - Intro and patient data
    ("# Kompleksowe Podsumowanie Medyczne Pacjenta", "index.md"),
    ("## Dane Pacjenta", "index.md"),

    # current-state.md - Active problems, medications, sensitivities
    ("## Lista Aktywnych Problemów", "current-state.md"),
    ("## Aktualne Leki i Suplementy", "current-state.md"),
    ("## Wrażliwość na Leki i Reakcje", "current-state.md"),
    ("## Status Szczepień", "current-state.md"),
    ("## Zalecenia Kliniczne dla Przyszłej Opieki", "current-state.md"),

    # visits.md - Medical history (will be reversed)
    ("## Chronologiczna Historia Medyczna", "visits.md"),
    ("## Historia Chirurgiczna/Proceduralna", "visits.md"),
    ("## Zaangażowane Placówki Weterynaryjne", "visits.md"),

    # lab-results.md - Lab trends and imaging (includes ### subsections)
    ("## Kluczowe Wartości Referencyjne w Czasie", "lab-results.md"),
    ("## Podsumowanie Badań w Kierunku Chorób Zakaźnych", "lab-results.md"),
    ("## Podsumowanie Badań Obrazowych", "lab-results.md"),

    # files.md - Document list
    ("## Spis Dokumentów Źródłowych", "files.md"),
    ("## Informacje o Dokumencie", "files.md"),
]

def load_pdf_mapping(mapping_file):
    """Load PDF filename to Google Drive ID mapping."""
    with open(mapping_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['pdf_mapping']

def anonymize_content(content):
    """Remove/anonymize private owner information."""
    lines = content.split('\n')
    result = []

    for line in lines:
        # Skip private information lines
        if '**Mikrochip**' in line or '**Paszport**' in line or '**Właściciel**' in line:
            continue
        result.append(line)

    return '\n'.join(result)

def replace_pdf_links(content, pdf_mapping):
    """Replace local PDF links with Google Drive links."""
    pattern = r'\[([^\]]+)\]\((?:\.?/?dokumentacja/)?([^)]+\.pdf)\)'

    def replace_func(match):
        link_text = match.group(1)
        filename = match.group(2)

        # Handle URL-encoded characters in filename
        decoded_filename = filename.replace('%20', ' ').replace('%2B', '+').replace('%3A', ':')

        # Try exact match first
        if decoded_filename in pdf_mapping:
            file_id = pdf_mapping[decoded_filename]
            drive_url = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"
            return f"[{link_text}]({drive_url})"

        # Try converting underscores to colons (2022_10_31 -> 2022:10:31 format)
        normalized = decoded_filename.replace('_', ':')
        if normalized in pdf_mapping:
            file_id = pdf_mapping[normalized]
            drive_url = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"
            return f"[{link_text}]({drive_url})"

        # Try case-insensitive and flexible matching
        decoded_lower = decoded_filename.lower().replace('_', ':')
        for key in pdf_mapping.keys():
            if key.lower().replace('_', ':') == decoded_lower:
                file_id = pdf_mapping[key]
                drive_url = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"
                return f"[{link_text}]({drive_url})"

        # Try removing trailing underscores and matching
        decoded_clean = decoded_filename.rstrip('_').lower().replace('_', ':')
        for key in pdf_mapping.keys():
            if key.rstrip('_').lower().replace('_', ':') == decoded_clean:
                file_id = pdf_mapping[key]
                drive_url = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"
                return f"[{link_text}]({drive_url})"

        # File not in mapping
        print(f"Warning: No mapping for '{decoded_filename}'")
        return f"[{link_text}](#) *(Dokument dostępny na życzenie)*"

    return re.sub(pattern, replace_func, content)

def split_by_headers(content):
    """Split content into sections by ## headers only.
    ### headers are kept within their parent ## section.
    """
    sections = {}
    current_header = "intro"
    current_content = []

    for line in content.split('\n'):
        # Only split on ## headers (not ###)
        if line.startswith('## ') and not line.startswith('### '):
            # Save previous section
            if current_content:
                sections[current_header] = '\n'.join(current_content)
            current_header = line.strip()
            current_content = [line]
        elif line.startswith('# ') and not line.startswith('##'):
            # Top-level header
            if current_content:
                sections[current_header] = '\n'.join(current_content)
            current_header = line.strip()
            current_content = [line]
        else:
            current_content.append(line)

    # Save last section
    if current_content:
        sections[current_header] = '\n'.join(current_content)

    return sections

def get_target_file(header):
    """Get target file for a section header."""
    for pattern, target in SECTION_MAPPING:
        if header == pattern or header.startswith(pattern):
            return target
    return None

def reverse_chronological_sections(content):
    """Reverse order of ### visit sections within ## Chronologiczna Historia."""
    lines = content.split('\n')
    result = []
    visit_sections = []
    current_visit = []
    in_chronological = False

    for line in lines:
        if '## Chronologiczna Historia Medyczna' in line:
            in_chronological = True
            result.append(line)
            continue

        if in_chronological:
            # Check for new ## section (end of chronological history)
            if line.startswith('## ') and 'Chronologiczna Historia' not in line:
                # Save last visit section
                if current_visit:
                    visit_sections.append('\n'.join(current_visit))
                # Add reversed visits
                for visit in reversed(visit_sections):
                    result.append(visit)
                # Reset and continue with new section
                in_chronological = False
                visit_sections = []
                current_visit = []
                result.append(line)
            # Check for ### visit header
            elif line.startswith('### '):
                if current_visit:
                    visit_sections.append('\n'.join(current_visit))
                current_visit = [line]
            else:
                current_visit.append(line)
        else:
            result.append(line)

    # Handle end of file
    if in_chronological and current_visit:
        visit_sections.append('\n'.join(current_visit))
        for visit in reversed(visit_sections):
            result.append(visit)

    return '\n'.join(result)

def remove_mermaid_blocks(content):
    """Remove Mermaid diagram blocks."""
    # Remove ```mermaid ... ``` blocks
    pattern = r'```mermaid[\s\S]*?```'
    return re.sub(pattern, '', content)

def generate_front_matter(page_name):
    """Generate Jekyll front matter for a page."""
    config = PAGE_CONFIG.get(page_name, {"title": page_name, "nav_order": 99})
    return f"""---
title: "{config['title']}"
nav_order: {config['nav_order']}
---

"""

def generate_navigation(page_name):
    """Generate footer navigation links."""
    pages = list(PAGE_CONFIG.keys())
    idx = pages.index(page_name) if page_name in pages else -1

    nav_parts = []

    if idx > 0:
        prev_page = pages[idx - 1]
        prev_title = PAGE_CONFIG[prev_page]['title']
        nav_parts.append(f"[← {prev_title}]({prev_page})")

    if page_name != "index.md":
        nav_parts.append("[Strona główna](index.md)")

    if idx < len(pages) - 1 and idx >= 0:
        next_page = pages[idx + 1]
        next_title = PAGE_CONFIG[next_page]['title']
        nav_parts.append(f"[{next_title} →]({next_page})")

    if nav_parts:
        return "\n\n---\n\n" + " | ".join(nav_parts) + "\n"
    return ""

def add_access_notice_and_toc(page_name):
    """Return notice about accessing private documents."""
    notice =  """{: .warning }
>📋 Dostęp do dokumentów
>
>Dokumenty medyczne do których odnośniki znajdują się na tej stronie znajdują się na prywatnym koncie Google Drive, aby chronić prywatność pacjenta.
>
>**Aby uzyskać dostęp do dokumentów wyślij email na adres:**
>**virhile(at)gmail.com**

---

"""
    # add TOC for files,lab-results,visits page
    if page_name == "files.md" or page_name == "lab-results.md" or page_name == "visits.md":
        notice += "- TOC\n{:toc}\n\n"
    return notice

def main():
    # Paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    docs_dir = repo_root / 'docs'
    original_file = repo_root.parent / 'podsumowanie-weterynaryjne.md'
    mapping_file = script_dir / 'pdf-mapping.json'

    if not original_file.exists():
        print(f"Error: Original file not found at {original_file}")
        return False

    if not mapping_file.exists():
        print(f"Error: PDF mapping file not found at {mapping_file}")
        return False

    # Load mapping
    print("Loading PDF mapping...")
    pdf_mapping = load_pdf_mapping(mapping_file)
    print(f"  Loaded {len(pdf_mapping)} PDF file mappings")

    # Read original content
    print("Reading original summary...")
    with open(original_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Process content globally first
    print("Anonymizing private information...")
    content = anonymize_content(content)

    print("Replacing PDF links with Google Drive links...")
    content = replace_pdf_links(content, pdf_mapping)

    print("Removing Mermaid diagrams...")
    content = remove_mermaid_blocks(content)

    print("Reversing chronological history (newest first)...")
    content = reverse_chronological_sections(content)

    # Split into sections
    print("Splitting content by headers...")
    sections = split_by_headers(content)
    print(f"  Found {len(sections)} sections")

    # Group sections by target file
    file_sections = {page: [] for page in PAGE_CONFIG.keys()}

    for header, section_content in sections.items():
        target = get_target_file(header)
        if target and target in file_sections:
            file_sections[target].append(section_content)
        elif header == "intro":
            # Intro goes to index.md
            file_sections["index.md"].insert(0, section_content)

    # Create docs directory
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Generate output files
    print("\nGenerating output files...")
    for page_name, page_sections in file_sections.items():
        if not page_sections:
            print(f"  Skipping {page_name} (no content)")
            continue

        output_path = docs_dir / page_name

        # Build page content
        page_content = generate_front_matter(page_name)
        page_content += add_access_notice_and_toc(page_name)
        page_content += '\n\n'.join(page_sections)

        # Add navigation
        page_content += generate_navigation(page_name)

        # Write file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(page_content)

        print(f"  Created {page_name}")

    print("\n Done! Generated files in docs/:")
    for page in PAGE_CONFIG.keys():
        output_path = docs_dir / page
        if output_path.exists():
            print(f"  - {page}")

    print("\nNext steps:")
    print("1. Review generated files in docs/")
    print("2. Run: git add -A && git commit -m 'Restructure: auto-split to multi-page' && git push")
    print("3. Visit https://Wojciechowski-Marcin.github.io/charlie-vet-page/")

    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
