---
name: annotrieve
description: Find, filter, compare and download eukaryotic genome annotations (GFF3) from Annotrieve (genome.crg.es/annotrieve) — via the annocli command-line tool, the Annotrieve REST API, and the annotrieve-xrefs gene-name search. Use this skill whenever the user wants genome annotations or GFF files for a species or clade, asks which annotations/assemblies exist for an organism or taxid, wants gene/transcript counts or BUSCO completeness across annotations, wants to slice a GFF by region/feature type, needs matching assembly FASTA with harmonised sequence names, or asks which species/annotations contain a given gene — even if they don't mention Annotrieve or annocli by name (e.g. "get me the honeybee GFF", "compare gene counts across Hymenoptera", "which ants have Pax6 annotated").
---

# Annotrieve

Annotrieve is a central catalogue of ~20,000 eukaryotic genome annotations (GFF3) aggregated from RefSeq, GenBank, Ensembl and community registries. Every annotation is re-indexed (sorted, bgzipped, CSI-indexed) and pre-profiled: feature types, biotypes, gene/transcript statistics and BUSCO scores are stored as metadata, so most questions can be answered **without downloading any GFF**.

Three interfaces, pick the lightest that answers the question:

| Need | Use |
|---|---|
| Download annotation files (+ assemblies, + sequence-name fixing) to disk | `annocli download` |
| Human-readable per-annotation summary / stats tables | `annocli summary`, `annocli stats` (`--tsv` for files) |
| Anything else: searching taxa, custom filters (BUSCO, database, date, assembly level), sorting, aggregates, metadata tables, GFF slices | REST API (`https://genome.crg.es/annotrieve/api/v0`) |
| "Which annotations contain gene X?" / genes inside one annotation | annotrieve-xrefs API (`https://genome.crg.es/annotrieve-xrefs/api/v1`) |

## Core concepts

- **annotation_id** = MD5 checksum of the uncompressed indexed GFF (32 hex chars). It is the primary key everywhere (annocli `--annotation-ids`, API `md5_checksums`, `/annotations/{id}/…`, xrefs).
- **taxid** = NCBI Taxonomy ID. Filters on `taxids` match the **whole lineage**, so a genus/order/class taxid returns every annotation below it (e.g. `7399` Hymenoptera → hundreds). This is usually what the user wants, but check counts before downloading.
- One species often has **several annotations** (different assemblies, and RefSeq + GenBank + Ensembl versions of the same assembly). When the user asks for "the" annotation of a species, narrow it down — typically `refseq_categories: "reference genome"` (annocli `--ref-only`), and/or prefer `db_sources: "RefSeq"` or `"Ensembl"` — and say what you chose.
- Users give names, not taxids. Resolve them first (see "Resolve a name to a taxid").

## Setup

annocli is a small Python package (depends only on `requests`):

```bash
annocli --version || pip install git+https://github.com/apollo994/annocli.git
```

The REST APIs need nothing but `curl` or Python `requests`. No authentication. Be polite: avoid hammering endpoints in tight loops (xrefs is rate-limited to ~3 req/s per IP); prefer one bulk call (e.g. `/annotations/report`) over many per-item calls.

## Workflow

1. **Resolve** names → taxids (or accept taxids / annotation IDs / assembly accessions from the user).
2. **Count before you fetch.** `annocli download --taxids X --mode prev`, or POST `/annotations` with `"limit": 1` and read `total`. If it's large (say > 50 files or several GB) tell the user and suggest narrowing (reference-only, one database, BUSCO threshold) before downloading.
3. **Answer from metadata where possible** — counts, BUSCO, feature types and gene stats are already in the API; don't download GFFs just to count genes.
4. **Download / slice** only what's needed.
5. **Report** what was selected and why (database, assembly, annotation_id), so the result is reproducible.

## annocli quick reference

Input (for `download`, `summary`, `stats`; taxid and annotation-ID inputs are mutually exclusive):
`--taxids 7460 9646` · `--taxids-file f.txt` · `--annotation-ids <md5> …` · `--annotation-ids-file f.txt`

```bash
annocli download --taxids 7460 --mode prev            # how many annotations would be fetched
annocli download --taxids 7460 --ref-only             # download reference-assembly annotations only
annocli download --taxids 7460 --ref-only --add-asm --fix-alias -o data/   # + genome FASTA, seq names harmonised
annocli download --taxids 7399 --mode links > get.sh  # wget commands instead of downloading
annocli summary --taxids 7460 --ref-only --tsv summary.tsv   # db, provider, release date, feature types, biotypes
annocli stats   --taxids 7460 --tsv stats.tsv              # gene/transcript counts and lengths
annocli alias annotation.gff3.gz assembly.fna.gz           # rename GFF seqids to match FASTA headers
```

Output layout: `<outdir>/<Organism_name>_<taxid>/<assembly_accession>/<Organism_name>_<taxid>_<database>_<assembly_accession>_<annotation_id>.gff.gz` (+ assembly `.fna.gz`, `.aliasMatch.gff.gz`, `.aliasMatch.gff.gz.aliasMappings.tsv`). Files are re-downloaded on every run (no skip-if-exists). Files are the *original source* GFFs (NCBI/Ensembl URLs). Full options and gotchas: `references/annocli.md`.

Use `--fix-alias` (or `annocli alias`) whenever the user will combine the GFF with the FASTA (e.g. bedtools, gffread, IGV): annotation seqids (e.g. `NC_037638.1`) frequently don't match FASTA headers from another source otherwise.

## REST API essentials

Base: `https://genome.crg.es/annotrieve/api/v0`. Full endpoint reference with response shapes: `references/api.md` — read it before using endpoints not shown here.

**Filtering.** List/stats endpoints accept the same filter set, either as query params (GET) or a JSON body (POST). If a JSON body is sent, query params are **ignored entirely** — put everything (filters, `limit`, `offset`) in one place. Multi-values are comma-separated strings (`"taxids": "7460,9646"`).

| Filter | Values / notes |
|---|---|
| `taxids` | lineage match (any rank) |
| `md5_checksums` | annotation IDs |
| `assembly_accessions` | `GCF_…` / `GCA_…` |
| `db_sources` | `RefSeq`, `GenBank`, `Ensembl`, `CommunityRegistry` |
| `refseq_categories` | `reference genome` (the "ref-only" filter) |
| `assembly_levels` | `Chromosome`, `Scaffold`, `Contig`, `Complete Genome` |
| `busco_complete_from` / `_to` | BUSCO complete %, e.g. `95` |
| `release_date_from` / `_to` | `YYYY-MM-DD` |
| `biotypes`, `feature_types`, `feature_sources` | annotation must contain these |
| `providers`, `pipelines`, `bioproject_accessions` | |
| `filter` | free-text on organism name / taxid / assembly name/accession |
| `sort_by` + `sort_order` | dot-path field, `asc`/`desc` (e.g. `busco.complete`, `source_file_info.release_date`) |
| `limit`, `offset` | default limit is **20**, max **1000** — always check `total` and paginate |
| `fields` | projection for `/annotations` (e.g. `annotation_id,organism_name,busco.complete`) — records are large (~5 KB), so project when listing many |

**The workhorse: `/annotations/report`** — returns *all* matching annotations as one TSV (no pagination). Default columns: `annotation_id, assembly_accession, assembly_name, organism_name, taxid, database, provider, source_url, bgzip_path, csi_path`. Add columns with `selected_fields` (comma string): `release_date, busco_complete, busco_lineage, coding_gene_count, coding_gene_length_mean, non_coding_gene_count, pseudogene_gene_count, feature_types, feature_biotypes, has_cds, has_exon, file_size, taxon_lineage, assembly_refseq_category, assembly_download_url, assembly_gc_percent`, … (full list in `references/api.md`).

```bash
curl -s -X POST https://genome.crg.es/annotrieve/api/v0/annotations/report \
  -H 'Content-Type: application/json' \
  -d '{"taxids":"7399","db_sources":"RefSeq","busco_complete_from":95,
       "selected_fields":"busco_complete,coding_gene_count,assembly_refseq_category"}' > hymenoptera.tsv
```

This is the fastest way to build comparison tables across a clade — prefer it over looping `annocli stats` or per-annotation calls.

**Other high-value endpoints**

- `POST /annotations` → paginated JSON records (`total`, `results`). Each record has `features_summary` (types, biotypes, attribute_keys, root_type_counts, has_cds…), `features_statistics` (per gene category and transcript type: counts, length/exon/CDS stats), `busco`, `source_file_info`, `indexed_file_info`.
- `GET /annotations/{id}` → one record.
- `POST /annotations/frequencies/{field}` → value counts over the filtered set. Fields: `taxid, organism_name, database, release_date, assembly_accession, assembly_name, feature_type, feature_source, biotype, pipeline, provider, attribute_key, busco_complete`.
- `POST /annotations/gene-stats`, `/transcript-stats`, `/busco-stats` → aggregates over the filtered set; `/{category}/{metric}` (+ `"include_annotations": true`) → raw per-annotation values for distributions.
- `GET /annotations/aggregates/taxons?rank=order` → per-taxon annotation counts and average gene counts (TSV-like `fields` + `rows`).
- `GET /annotations/{id}/gff?region=…&start=…&end=…&feature_type=…&biotype=…&feature_source=…` → streamed GFF lines of the indexed file. **At least one filter is required** (otherwise 400 — download the whole file instead). `region` accepts chromosome aliases (`chr1`, `NC_037638.1`, `CM009931.2` all work); values for `feature_type`/`biotype` must exist in that annotation's `features_summary` (the 400 message lists valid ones).
- `GET /annotations/{id}/contigs` → seqids in the GFF (plain text).
- Taxonomy: `GET /taxons?filter=apis`, `/taxons/{taxid}`, `/taxons/{taxid}/children`, `/taxons/{taxid}/ancestors`.
- Assemblies: `GET /assemblies/{accession}` (level, stats, `download_url`, refseq_category), `/assemblies/{accession}/chr-aliases` (TSV of sequence-name equivalents), `POST /assemblies` with the same style of filters.

**Indexed (sorted, bgzipped + CSI) files** are served at `https://genome.crg.es/annotrieve/files{bgzip_path}` (and `{csi_path}`), paths from the record or report. Use these when the user wants tabix-ready files or for genome browsers; annocli downloads the original source files instead.

## Resolve a name to a taxid

```bash
curl -s 'https://genome.crg.es/annotrieve/api/v0/taxons?filter=apis&limit=10'           # scientific names, any rank
curl -s 'https://genome.crg.es/annotrieve/api/v0/organisms?filter=honey%20bee&limit=10'  # also matches common names
```

Results include `taxid`, `scientific_name`, `rank`, `annotations_count`. `filter` is a case-insensitive substring match, so check `rank` and pick the exact name; if ambiguous, show the user the candidates. Only taxa with annotations in Annotrieve are returned — no hit means no annotation, not a typo (but do try the common-name route via `/organisms`).

## Gene-name search (annotrieve-xrefs)

Base: `https://genome.crg.es/annotrieve-xrefs/api/v1`. Matches gene **symbols and aliases**, case-insensitive; trailing `*` = prefix (≥3 chars before `*`).

```bash
curl -s 'https://genome.crg.es/annotrieve-xrefs/api/v1/hits?names=Pax6,eyeless&include_taxids=7399&match=any'
```

Response is compact: `fields` + `rows` (`[annotation_id, taxid, source, n_matched, matched]`). Join `annotation_id`s back to Annotrieve (`/annotations/report` with `md5_checksums`) for organism names. Drill into one annotation: `GET /annotations/{id}/genes?names=Pax6` → `local_id` → `/annotations/{id}/genes/{local_id}` (coordinates) and `…/xrefs`. Absence of a hit means the symbol isn't in that GFF's names/aliases — not that the gene is biologically absent (many annotations use `LOC…` IDs). Say so when reporting negatives. Details and limits: `references/xrefs.md`.

## Gotchas worth remembering

- Default page size is 20. A `total` larger than `len(results)` means you're missing data.
- Higher-rank taxids explode quickly (Insecta, Mammalia → thousands of annotations, many GB). Always preview.
- Many species have duplicate annotations of the *same* assembly from RefSeq and GenBank; deduplicate by `assembly_accession` when counting species or comparing.
- `features_statistics` and `busco` can be missing/empty for some annotations; handle nulls rather than assuming 0.
- annocli `--ref-only` filters on NCBI's "reference genome" category; species without a designated reference assembly return nothing — fall back to choosing by database/assembly level and tell the user.
- For a user-uploaded GFF (not in the catalogue) see `POST /annotations/upload-gff` in `references/api.md`.
- `/jobs/*` endpoints are admin-only — never call them.
