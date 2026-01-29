#!/usr/bin/env python3
"""
Script to anonymize the veterinary summary and replace PDF links with Google Drive links.
"""

import json
import re
from pathlib import Path

def load_pdf_mapping(mapping_file):
    """Load PDF filename to Google Drive ID mapping."""
    with open(mapping_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['pdf_mapping']

def anonymize_content(content):
    """Remove/anonymize private owner information."""
    # Remove microchip, passport, and owner name rows from the table
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
    # Pattern to match: [text](dokumentacja/filename.pdf) or [text](./dokumentacja/filename.pdf)
    pattern = r'\[([^\]]+)\]\((?:\.?/?dokumentacja/)?([^)]+\.pdf)\)'

    def replace_func(match):
        link_text = match.group(1)
        filename = match.group(2)

        # Handle URL-encoded characters in filename
        decoded_filename = filename.replace('%20', ' ').replace('%2B', '+').replace('%3A', ':')

        # Try exact match first
        if decoded_filename in pdf_mapping:
            file_id = pdf_mapping[decoded_filename]
            # Create Google Drive link
            drive_url = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"
            return f"[{link_text}]({drive_url})"

        # Try converting underscores to colons (2022_10_31 -> 2022:10:31 format)
        normalized = decoded_filename.replace('_', ':')
        if normalized in pdf_mapping:
            file_id = pdf_mapping[normalized]
            drive_url = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"
            return f"[{link_text}]({drive_url})"

        # Try case-insensitive and flexible matching, also normalize underscores
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

        # File not in mapping - show helpful message
        print(f"Warning: No mapping for '{decoded_filename}'")
        # Try to find similar names
        similar = [k for k in pdf_mapping.keys() if decoded_filename.lower().replace('_', ' ') in k.lower().replace('_', ' ') or k.lower().replace('_', ' ') in decoded_filename.lower().replace('_', ' ')]
        if similar:
            print(f"  Similar files found: {similar}")
        return f"[{link_text}](#) *(Document available upon request)*"

    return re.sub(pattern, replace_func, content)

def add_access_notice(content):
    """Add notice about accessing private documents."""
    notice = """---

## 📋 About Accessing Medical Documents

The medical documents linked on this page are stored in a private Google Drive folder to protect patient privacy.

**To request access to any document:**
- Email: **virhile@gmail.com**
- Subject: "Request for Charlie's medical document access"
- Include which document(s) you need

Access is granted on a case-by-case basis for legitimate veterinary, educational, or research purposes.

---
"""
    return content + "\n" + notice

def main():
    # Paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    source_file = repo_root / 'docs' / 'index.md'
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

    # Process content
    print("Anonymizing private information...")
    content = anonymize_content(content)

    print("Replacing PDF links with Google Drive links...")
    content = replace_pdf_links(content, pdf_mapping)

    print("Adding access notice...")
    content = add_access_notice(content)

    # Write to docs folder
    print(f"Writing processed content to {source_file}...")
    source_file.parent.mkdir(parents=True, exist_ok=True)
    with open(source_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("\n✓ Done! The docs/index.md file has been created.")
    print("\nNext steps:")
    print("1. Review docs/index.md to ensure anonymization is correct")
    print("2. Commit and push to GitHub")
    print("3. Enable GitHub Pages in repository settings")
    print("4. Visit https://Wojciechowski-Marcin.github.io/charlie-vet-page/")

    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
