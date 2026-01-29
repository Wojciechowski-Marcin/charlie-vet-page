# Charlie's Medical History - Public Website

This repository hosts a public-facing website with anonymized veterinary medical documentation for a cat named Charlie.

## About This Site

Charlie is a 10-year-old Egyptian Mau/mixed breed cat with a complex medical history spanning 2022-2026. This site provides:

- **Chronological Medical History**: Detailed timeline of treatments, consultations, and diagnoses
- **Test Results**: Laboratory findings, imaging reports, and specialized testing
- **Medical Conditions**: Documentation of conditions managed and resolved over time
- **Veterinary Team**: Information about the specialized clinics involved in Charlie's care

## Accessing Medical Documents

Medical documents (PDFs) are stored privately to protect patient privacy. To request access:

**Email**: virhile@gmail.com
**Subject**: "Request for Charlie's medical documentation"

Access is granted on a case-by-case basis for legitimate veterinary, educational, or research purposes.

## Privacy & Anonymization

This website contains:
- ✓ Detailed medical information (for veterinary education/reference)
- ✓ Veterinary clinic names and general information
- ✗ Owner names and personal identifiers (anonymized)
- ✗ Microchip/passport numbers (removed)
- ✗ PDF documents (private, accessible by request only)

## Technologies

- **GitHub Pages**: Hosting
- **Jekyll**: Static site generator with minimal theme
- **Markdown**: Content format

## Building Locally (Optional)

```bash
# Install Ruby and Jekyll
gem install jekyll bundler

# Navigate to docs folder
cd docs

# Serve locally
bundle exec jekyll serve

# Visit http://localhost:4000
```

## Content Generation

The website content is generated from anonymized medical records using:

```bash
# From the repository root
python3 scripts/replace-pdf-links.py
```

This script:
1. Reads the original veterinary summary
2. Removes private owner information
3. Replaces local PDF links with Google Drive links
4. Creates the public `docs/index.md` file

## Repository Structure

```
charlie-vet-page/
├── docs/
│   ├── index.md           (Public medical summary)
│   ├── _config.yml        (Jekyll configuration)
│   └── assets/
│       └── css/
├── scripts/
│   ├── pdf-mapping.json   (PDF → Google Drive ID mapping)
│   └── replace-pdf-links.py (Content generation script)
├── .gitignore            (Prevent PDF commits)
└── README.md
```

## Contributing

This is a read-only informational site. No contributions are accepted.

## Contact

For questions about Charlie's medical history or to request document access:
**Email**: virhile@gmail.com

---

*Website generated for veterinary reference and educational purposes.*
