# annocli Usage Guide

This guide provides detailed usage examples for the `download` and `alias` commands in annocli.

## Download Command

The `download` command allows you to query and download genome annotations for specified taxonomy IDs (taxids).

### Basic Usage

Download annotations for a single species:

```bash
annocli download 9606
```

Download annotations for multiple taxids:

```bash
annocli download 9606 10090 10116
```

### Options

- `--mode`: Choose the operation mode
  - `dw` (default): Download files
  - `prev`: Preview the number of available annotations
  - `links`: Print wget commands instead of downloading

- `--ref_only`: Download only annotations from reference genome assemblies

- `--add_asm`: Also download the corresponding assembly files

- `--fix_alias`: Match sequence names with assembly (requires `--add_asm`)

- `-o, --output`: Specify output folder (default: `annotation_downloads`)

### Examples

#### Preview Mode

Check how many annotations are available for human (taxid 9606):

```bash
annocli download 9606 --mode prev
```

Output:
```
Taxids:              [9606]
Annotations:         45
Only reference:      False
Include assemblies:  False
```

#### Download with Assemblies

Download annotations and assemblies for human, including alias matching:

```bash
annocli download 9606 --add_asm --fix_alias
```

This will:
- Download annotation GFF files
- Download corresponding assembly FASTA files
- Create alias-matched versions of the annotations where sequence IDs match the assembly

#### Download Links Only

Generate wget commands for downloading annotations:

```bash
annocli download 9606 --mode links
```

Output:
```
mkdir -p annotation_downloads/Homo_sapiens_9606/GCF_000001405.40
wget https://... -O annotation_downloads/Homo_sapiens_9606/GCF_000001405.40/Homo_sapiens_9606_RefSeq_GCF_000001405.40_109.20211119.gff3.gz
```

#### Reference Only

Download only reference genome annotations:

```bash
annocli download 9606 --ref_only
```

### Output Structure

Downloaded files are organized as:

```
annotation_downloads/
├── Organism_name_taxid/
│   └── Assembly_accession/
│       ├── annotation_file.gff3.gz
│       ├── assembly_file.fna.gz (if --add_asm)
│       ├── annotation_file.aliasMatch.gff3.gz (if --fix_alias)
│       └── annotation_file.aliasMatch.gff3.gz.aliasMappings.tsv (if --fix_alias)
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

Match aliases between an annotation and assembly:

```bash
annocli alias annotation.gff3.gz assembly.fna.gz
```

This will create:
- `annotation.aliasMatch.gff3.gz`: The annotation with sequence IDs matched to the assembly
- `annotation.aliasMatch.gff3.gz.aliasMappings.tsv`: A tab-separated file showing the original -> alias mappings

### How It Works

The alias command:

1. Extracts sequence names from the assembly FASTA file
2. Parses the "region" lines in the GFF annotation to find Alias attributes
3. Creates a mapping from original sequence IDs to their aliases
4. Rewrites the GFF file with matched sequence IDs
5. Generates a report of the mappings

This ensures that the sequence IDs in the annotation match those in the assembly, which is important for tools that require consistent naming.

## Summary Command

The `summary` command provides information about features and biotypes available in annotations for specified taxonomy IDs.

### Usage

```bash
annocli summary <taxids> [--ref_only]
```

### Parameters

- `taxids`: Taxonomy IDs (required, one or more integers)
- `--ref_only`: Show only annotations from reference genome assemblies (optional)
- `--tsv`: File to save annotation summary in tsv format (optional)

### Example

Get information about annotations for human (taxid 9606):

```bash
annocli summary 9606
```

### Output

For each annotation, the command prints a detailed summary including:

- Organism name and TaxID
- Assembly accession and name
- Database and URL
- Release date
- Feature availability (biotype, CDS, exon)
- Lists of types, sources, biotypes, and missing IDs
- Root type counts (features with no children)

This helps users understand what features are available before downloading annotations.
