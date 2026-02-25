# annocli Usage Guide

This guide provides detailed usage examples annocli commands.

- [`download`](USAGE.md#download-command): Download annotations from Annotrive 
- [`alias`](USAGE.md#alias-command): Match sequence IDs between annotation and assembly files
- [`summary`](USAGE.md#summary-command): Get information about features and biotypes available
- [`stats`](USAGE.md#stats-command): Get summary statistics about gene and transcript features

## Input Methods

`download`, `summary` and `stats` support two types of input.
- [NCBI taxonomic identifier](https://www.ncbi.nlm.nih.gov/taxonomy)
- [Annotrive annotation ID](https://genome.crg.es/annotrieve/)
At least one must be provided, and taxid inputs and annotation ID inputs are mutually exclusive.

| Option | Description |
|--------|-------------|
| `--taxids` | One or more taxonomy IDs (space-separated integers) |
| `--taxids-file` | Path to a plain-text file with one taxonomy ID per line |
| `--annotation-ids` | One or more Annotrieve annotation IDs (md5 checksums, space-separated) |
| `--annotation-ids-file` | Path to a plain-text file with one annotation ID per line |

**Examples:**

```bash
# By taxid(s)
annocli download --taxids 9646
annocli download --taxids 9646 10090 10116

# By taxids file
annocli download --taxids-file my_taxids.txt

# By annotation ID(s)
annocli download --annotation-ids 1d7a323a9ccc520dc1dba53fd58466fd

# By annotation IDs file
annocli download --annotation-ids-file my_annotation_ids.txt
```

## Download Command

The `download` command queries and downloads genome annotations.

### Basic Usage

```bash
annocli download --taxids <taxid> [options]
annocli download --annotation-ids <annotation_id> [options]
```

### Options

- `--taxids`: Taxonomy IDs (space-separated)
- `--taxids-file`: Path to file with taxonomy IDs, one per line
- `--annotation-ids`: Annotation IDs from Annotrieve (md5 checksums, space-separated)
- `--annotation-ids-file`: Path to file with annotation IDs, one per line
- `--mode`: Choose the operation mode
  - `dw` (default): Download files
  - `prev`: Preview the number of available annotations
  - `links`: Print wget commands instead of downloading
- `--ref-only`: Download only annotations from reference genome assemblies
- `--add-asm`: Also download the corresponding assembly files
- `--fix-alias`: Match sequence names with assembly (requires `--add-asm`)
- `-o, --output`: Specify output folder (default: `annotation_downloads`)

### Examples

#### Preview Mode

```bash
annocli download --taxids 9646 --mode prev
```

Output:
```
Annotations:         3
Only reference:      False
Include assemblies:  False
```

#### Download with Assemblies

```bash
annocli download --taxids 7460 --add-asm --fix-alias
```

#### Download Links Only

```bash
annocli download --taxids 7460 --mode links
```

#### Reference Annotations Only

```bash
annocli download --taxids 7460 --ref-only
```

#### By Annotation ID

```bash
annocli download --annotation-ids 1d7a323a9ccc520dc1dba53fd58466fd
```

### Output Structure

```
annotation_downloads/
├── Organism_name_taxid/
│   └── Assembly_accession/
│       ├── annotation_file.gff3.gz
│       ├── assembly_file.fna.gz (if --add-asm)
│       ├── annotation_file.aliasMatch.gff3.gz (if --fix-alias)
│       └── annotation_file.aliasMatch.gff3.gz.aliasMappings.tsv (if --fix-alias)
```

## Alias Command

The `alias` command matches sequence IDs between annotation GFF files and assembly FASTA files.

### Usage

```bash
annocli alias <annotation_file> <assembly_file> [--output <output_file>]
```

### Parameters

- `annotation_file`: Path to the annotation GFF file (can be .gff3 or .gff3.gz)
- `assembly_file`: Path to the assembly FASTA file (can be .fna or .fna.gz)
- `--output`: Optional output path for the updated annotation file (default: auto-generated with .aliasMatch. suffix)

### Example

```bash
annocli alias annotation.gff3.gz assembly.fna.gz
```

This will create:
- `annotation.aliasMatch.gff3.gz`: The annotation with sequence IDs matched to the assembly
- `annotation.aliasMatch.gff3.gz.aliasMappings.tsv`: A tab-separated file showing the original -> alias mappings

### How It Works

1. Extracts sequence names from the assembly FASTA file
2. Parses the "region" lines in the GFF annotation to find Alias attributes
3. Creates a mapping from original sequence IDs to their aliases
4. Rewrites the GFF file with matched sequence IDs
5. Generates a report of the mappings

## Summary Command

The `summary` command provides information about features and biotypes available in annotations.

### Usage

```bash
annocli summary --taxids <taxid> [--ref-only] [--tsv <file>]
annocli summary --annotation-ids <annotation_id> [--tsv <file>]
```

### Options

- `--taxids`: Taxonomy IDs (space-separated)
- `--taxids-file`: Path to file with taxonomy IDs, one per line
- `--annotation-ids`: Annotation IDs from Annotrieve (md5 checksums, space-separated)
- `--annotation-ids-file`: Path to file with annotation IDs, one per line
- `--ref-only`: Show only annotations from reference genome assemblies (optional)
- `--tsv`: File to save annotation summary in tsv format (optional)

### Examples

```bash
annocli summary --taxids 7460

annocli summary --taxids 7460 --ref-only

annocli summary --annotation-ids 1d7a323a9ccc520dc1dba53fd58466fd

annocli summary --taxids 7460 --ref-only --tsv summary.tsv
```

### Output

For each annotation, prints a detailed summary including organism name, TaxID, assembly accession, database, release date, feature availability (biotype, CDS, exon), and root type counts.

## Stats Command

The `stats` command provides quantitative statistics about gene and transcript features in annotations.

### Usage

```bash
annocli stats --taxids <taxid> [--ref-only] [--tsv <file>]
annocli stats --annotation-ids <annotation_id> [--tsv <file>]
```

### Options

- `--taxids`: Taxonomy IDs (space-separated)
- `--taxids-file`: Path to file with taxonomy IDs, one per line
- `--annotation-ids`: Annotation IDs from Annotrieve (md5 checksums, space-separated)
- `--annotation-ids-file`: Path to file with annotation IDs, one per line
- `--ref-only`: Consider only annotations from reference genome assemblies (optional)
- `--tsv`: File to save annotation statistics in tsv format (optional)

### Examples

```bash
annocli stats --taxids 7460

annocli stats --taxids 7460 --ref-only --tsv bee_stats.tsv

annocli stats --annotation-ids 1d7a323a9ccc520dc1dba53fd58466fd
```

### Output

For each annotation, displays gene and transcript statistics including lengths, distributions, feature counts, and statistical summaries (mean, min, max).


