# Assets Directory - SAC System

This directory contains static assets used by the Excel reporting system.

## Structure

```
assets/
├── logo_chedraui.png     # Corporate logo (150x50px recommended)
├── templates/            # Excel template files
│   └── corporate_header.xlsx
└── README.md
```

## Logo Requirements

The logo file `logo_chedraui.png` should be:
- Format: PNG with transparent background
- Dimensions: 150x50 pixels (recommended)
- Location: Place in this directory

## Usage

The logo is automatically used by:
- `ExcelTemplate.add_logo()` method
- Dashboard reports
- Corporate headers

## Adding Custom Templates

Place Excel template files in the `templates/` subdirectory.
These can be used as base templates for custom reports.

---
Sistema SAC - CEDIS Cancún 427
