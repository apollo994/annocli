# annocli Development Guide

## Project Overview

`annocli` is a Python command-line tool for querying and downloading genome annotations from the [Annotrieve API](https://genome.crg.es/annotrieve/). It provides four main commands for working with genomic data:

- **download**: Download annotations for taxonomy IDs (with assembly support)
- **alias**: Match sequence IDs between annotation GFF files and assembly FASTA files
- **summary**: Get feature and biotype information about annotations
- **stats**: Get statistical information about gene and transcript features

## Build, Test, and Lint Commands

### Installation
```bash
pip install -e .
```

### Testing
```bash
# Run the smoke test suite (uses Giant Panda taxid 9646)
./test.sh

# Test specific commands manually
annocli --help
annocli download 9646 --mode prev
annocli summary 9646 --ref_only
```

**Note**: No automated unit test framework is configured. Testing is done via the `test.sh` smoke test script.

## Architecture

### CLI Entry Point
- Entry: `src/annocli/cli.py:main()` 
- Uses `argparse` with subparsers for each command
- All commands share a common API request pattern via `request_params` dict

### Core Modules (`src/annocli/core/`)
- **requests.py**: Central API communication with Annotrieve API
  - Base URL: `https://genome.crg.es/annotrieve/api/v0`
  - `core_request()`: Base HTTP wrapper
  - `make_request()`: Higher-level API interface
- **download_helpers.py**: Download command logic
- **alias_helpers.py**: Sequence ID matching between GFF and FASTA
- **summary_helpers.py**: Feature/biotype information retrieval
- **stats_helpers.py**: Statistical analysis of annotations
- **general_helpers.py**: Shared utilities

### Key Data Flow
1. CLI parses args and builds `request_params` dict (limit, taxids, refseq_categories)
2. Command handlers receive `args` and `request_params`
3. Handlers call `core_request()` or `make_request()` to query Annotrieve API
4. Response data is processed and displayed/downloaded

## Key Conventions

### Request Parameter Pattern
Commands that query the API follow a consistent pattern in `cli.py`:
```python
REQUEST_LIMIT = 1000
request_params = {
    "limit": REQUEST_LIMIT,
    **({"taxids": args.taxids} if args.taxids else {}),
    **({"refseq_categories": "reference genome"} if args.ref_only else {}),
}
```

### File Naming Conventions
- Annotation files: `{organism}_{taxid}_{database}_{accession}_{version}.gff3.gz`
- Assembly files: `{organism}_{taxid}_{database}_{accession}_{version}.fna.gz`
- Alias-matched files: Original filename with `.aliasMatch.` suffix inserted before extension
- Alias mappings: `{aliasMatch_file}.aliasMappings.tsv`

### Directory Structure for Downloads
```
annotation_downloads/
└── {Organism_name}_{taxid}/
    └── {Assembly_accession}/
        ├── {annotation}.gff3.gz
        ├── {assembly}.fna.gz (if --add_asm)
        ├── {annotation}.aliasMatch.gff3.gz (if --fix_alias)
        └── {annotation}.aliasMatch.gff3.gz.aliasMappings.tsv (if --fix_alias)
```

### Compressed File Handling
The `alias` command handles both compressed (.gz) and uncompressed files:
- Uses subprocess with bash commands (`gzip -cd` or `cat`)
- Detection based on file extension
- Output format matches input compression

### Taxonomy IDs (taxids)
- Can be species-level or higher taxonomic groups
- Multiple taxids accepted as space-separated arguments
- Test organism: Giant Panda (taxid 9646)

## API Integration

### Annotrieve API Endpoints
- All requests go through `core_request()` in `requests.py`
- Default request limit: 1000 items
- Filtering: `taxids`, `refseq_categories` ("reference genome")

### Error Handling
- `core_request()` wraps `requests.exceptions.RequestException`
- Raises `ValueError` with descriptive messages
- JSON decode errors also caught and re-raised

## Development Notes

- Version defined in both `pyproject.toml` and `cli.py` (keep synchronized)
- No linting configuration present
- No dependencies listed in `pyproject.toml` (but uses `requests` library)
- Smoke test uses temp directory `/tmp/annocli_smoke_test_$$` with automatic cleanup
