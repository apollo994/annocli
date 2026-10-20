# annocli reference

Source: https://github.com/apollo994/annocli · Install: `pip install git+https://github.com/apollo994/annocli.git` · Help: `annocli <command> --help`

annocli is a thin client over the Annotrieve API. Use it for downloading files and quick human-readable tables; drop to the REST API (`api.md`) for anything it doesn't expose (BUSCO/date/database filters, sorting, custom columns).

## Input options (download, summary, stats)

Exactly one input kind: taxids **or** annotation IDs (mutually exclusive).

| Option | |
|---|---|
| `--taxids 7460 9646` | space-separated; any rank (lineage match) |
| `--taxids-file ids.txt` | one per line |
| `--annotation-ids <md5> …` | 32-hex annotation IDs |
| `--annotation-ids-file ids.txt` | one per line |

Every ID is validated first with one API call each (`[INFO] taxid 7460: 3 annotation(s) found` / `[WARNING] … no annotations found, skipping` on stderr). Invalid IDs are skipped, not fatal — check stderr. If none are valid, it exits.

## download

```
annocli download <input> [--mode dw|prev|links] [--ref-only] [--add-asm] [--fix-alias] [-o DIR]
```

| Option | |
|---|---|
| `--mode dw` (default) | download files |
| `--mode prev` | print count only (`Annotations: N`) — run this first |
| `--mode links` | print `mkdir`/`wget` commands (+ `annocli alias` lines with `--fix-alias`) to stdout; good for HPC/batch jobs or letting the user review |
| `--ref-only` | only annotations on NCBI "reference genome" assemblies |
| `--add-asm` | also download the genomic FASTA of the annotated assembly |
| `--fix-alias` | rewrite GFF seqids to the FASTA's sequence names; requires `--add-asm` |
| `-o, --output` | output folder (default `annotation_downloads`) |

Output:
```
<DIR>/<Organism_name>_<taxid>/<assembly_accession>/
    <Organism_name>_<taxid>_<database>_<assembly_accession>_<annotation_id>.gff.gz
    <assembly FASTA filename from NCBI>.fna.gz                  (--add-asm)
    <…>.aliasMatch.gff.gz                                        (--fix-alias)
    <…>.aliasMatch.gff.gz.aliasMappings.tsv                      (--fix-alias; original → new seqid)
```

Behaviour to know:
- Downloads the **original source** GFF (NCBI/Ensembl URL), not Annotrieve's re-indexed copy. For the sorted/bgzipped/CSI version use `bgzip_path` from the API.
- No resume / skip-if-exists: rerunning re-downloads everything. For big sets prefer `--mode links` and run the `wget` script (`wget -c` can be added).
- Downloads are sequential; hundreds of annotations can take a long time and many GB (vertebrate GFFs are often 30–100 MB compressed, FASTAs 1 GB+).
- `[WARNING] Assembly not found` → no FASTA URL known for that assembly; the GFF is still downloaded.

## summary

```
annocli summary <input> [--ref-only] [--tsv FILE]
```
Per annotation: organism, taxid, assembly, database, provider, release date, source URL, has biotype/CDS/exon, root-type counts, printed per annotation. `--tsv` writes one row per annotation, including feature type / source / biotype columns.

## stats

```
annocli stats <input> [--ref-only] [--tsv FILE]
```
Per annotation: gene counts and length stats per category (coding, non-coding, pseudogene) and transcript-type stats (counts, lengths, exons, CDS); printed per annotation. `--tsv` writes one row per annotation (all-NA columns dropped).

For cross-species comparison tables with specific columns, `/annotations/report` with `selected_fields` is usually faster and cleaner than parsing `stats` output.

## alias

```
annocli alias ANNOTATION.gff[.gz] ASSEMBLY.fna[.gz] [--output OUT.gff.gz]
```
Renames GFF column-1 seqids to the names used in the FASTA. Resolution ladder (no renaming on ambiguous guesses):
0. seqid already in FASTA → unchanged
1. `Alias=` attribute of the GFF `region` feature (NCBI/Ensembl GFFs have these)
2. normalisation: INSDC version suffix (`CM113805` ↔ `CM113805.1`), `chr` prefix, mitochondrion spellings (`MT`, `M`, `mito`), case

Writes `<annotation>.aliasMatch.<ext>` and `<…>.aliasMappings.tsv`. Unresolved seqids are kept as-is and reported. Works on any GFF/FASTA pair, not just Annotrieve downloads.
