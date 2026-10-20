# Annotrieve REST API reference

Base URL: `https://genome.crg.es/annotrieve/api/v0` · OpenAPI JSON: `/openapi.json` · Interactive docs: https://genome.crg.es/annotrieve/api-docs/

The OpenAPI spec declares request bodies as free-form objects, so it does **not** list the filters. This file does (derived from the server source, github.com/guigolab/annotrieve, `server/helpers/annotation.py` and `server/helpers/constants.py`).

## Contents
1. Conventions
2. Annotation filters
3. Annotation endpoints
4. Report (TSV) columns
5. Stats endpoints
6. GFF slicing, contigs
7. Assemblies
8. Taxonomy & organisms
9. BioProjects
10. Uploading a custom GFF
11. Annotation record shape

## 1. Conventions

- Most list/stat endpoints exist as both `GET` (filters as query params) and `POST` (filters as JSON body). **If a JSON body is present, query params are ignored.** Prefer POST + JSON for anything non-trivial.
- Multi-value filters are comma-separated strings: `"taxids": "7460,9646"`. Values containing commas can be CSV-quoted: `"providers": "\"Hiller Lab, Senckenberg\""`. JSON lists also work.
- Paginated responses: `{"total": N, "offset": o, "limit": l, "results": [...]}`. Default `limit` 20. Loop with `offset` until `offset >= total`, or set `limit` up to the maximum of **1000** (larger → 400) combined with `fields` projection.
- Errors: `{"detail": "message"}` with 400/404/500.
- Booleans as strings in query params: `has_stats=true`.

## 2. Annotation filters

Accepted by `/annotations`, `/annotations/report`, `/annotations/frequencies/{field}`, `/annotations/gene-stats*`, `/annotations/transcript-stats*`, `/annotations/busco-stats*`.

| Key | Meaning |
|---|---|
| `taxids` | Lineage match: annotation's `taxon_lineage` contains any listed taxid |
| `md5_checksums` | Annotation IDs |
| `assembly_accessions` | GCA/GCF accessions |
| `db_sources` | `RefSeq`, `GenBank`, `Ensembl`, `CommunityRegistry` |
| `providers` | e.g. `NCBI RefSeq`, `Ensembl`, `Beijing Genomics Institute, Shenzhen` (see `/annotations/frequencies/provider`) |
| `pipelines` | source pipeline name (see `/annotations/frequencies/pipeline`) |
| `feature_types` | annotation contains GFF col-3 types (e.g. `mRNA,lnc_RNA`) |
| `feature_sources` | GFF col-2 sources (e.g. `Gnomon`, `BestRefSeq`) |
| `biotypes` | biotypes present (e.g. `protein_coding,lncRNA`) |
| `has_stats` | `true` → only annotations with computed feature statistics |
| `release_date_from`, `release_date_to` | `YYYY-MM-DD` |
| `busco_complete_from`, `busco_complete_to` | float, BUSCO complete % |
| `refseq_categories` | assembly-side: `reference genome` |
| `assembly_levels` | assembly-side: `Chromosome`, `Scaffold`, `Contig`, `Complete Genome` |
| `assembly_statuses`, `assembly_types` | assembly-side (e.g. `current`; `haploid`, `alternate-pseudohaplotype`…) |
| `bioproject_accessions` | assembly-side: PRJNA…/PRJEB… |
| `filter` | case-insensitive substring over taxid, organism name, assembly name, assembly accession |
| `sort_by`, `sort_order` | any record path in dot notation; `asc` (default) / `desc` |
| `limit`, `offset` | pagination (`/annotations` only) |
| `fields` | projection for `/annotations` — comma list of dot paths |
| `selected_fields` | extra TSV columns for `/annotations/report` |

Discover valid values for a filter with `/annotations/frequencies/{field}` on the current filtered set.

## 3. Annotation endpoints

| Method & path | Returns |
|---|---|
| `GET/POST /annotations` | paginated records |
| `GET /annotations/{md5}` | one record |
| `GET/POST /annotations/report` | TSV of all matches, header row first, no pagination |
| `GET /annotations/frequencies` | `{"fields": [...]}` allowed frequency fields |
| `GET/POST /annotations/frequencies/{field}` | `{"value": count, ...}`. Fields: `taxid, organism_name, database, release_date, assembly_accession, assembly_name, feature_type, feature_source, biotype, pipeline, provider, attribute_key, busco_complete` |
| `GET /annotations/aggregates/taxons?rank=<rank>` | `{"fields": ["taxid","taxon_name","annotations_count","avg_coding_genes_count","avg_non_coding_genes_count","avg_pseudogenes_count"], "rows": [...]}` for all taxa of that rank (whole catalogue; no filters) |
| `GET /annotations/errors?limit=&offset=` | annotations that failed processing (with error messages) |
| `GET /annotations/{md5}/gff?…` | streamed GFF lines (see §6) |
| `GET /annotations/{md5}/contigs` | plain-text seqids |
| `GET /annotations/{md5}/contigs/aliases` | paginated `{sequence_id, aliases}` |

Example — the 5 most complete RefSeq bee annotations:
```bash
curl -s -X POST $B/annotations -H 'Content-Type: application/json' -d '{
  "taxids":"7458","db_sources":"RefSeq","sort_by":"busco.complete","sort_order":"desc",
  "limit":5,"fields":"annotation_id,organism_name,assembly_accession,busco.complete"}'
```

## 4. Report (TSV) columns

Default columns (always present, in this order): `annotation_id, assembly_accession, assembly_name, organism_name, taxid, database, provider, source_url, bgzip_path, csi_path`.

Extra columns via `selected_fields` (comma string; appended in the order given):

- Taxonomy: `taxon_lineage`
- Source file: `release_date, last_modified, source_md5, source_pipeline_name, source_pipeline_version, source_pipeline_method`
- Indexed file: `file_size, processed_at, indexed_md5, indexed_pipeline_name, indexed_pipeline_version, indexed_pipeline_method`
- BUSCO: `busco_lineage, busco_version, busco_total_count, busco_complete, busco_single_copy, busco_duplicated, busco_fragmented, busco_missing`
- Feature summary: `has_biotype, has_cds, has_exon, feature_types, feature_sources, feature_biotypes, attribute_keys, types_missing_id, root_type_counts`
- Gene stats: `coding_gene_count, coding_gene_length_mean, non_coding_gene_count, non_coding_gene_length_mean, pseudogene_gene_count, pseudogene_gene_length_mean`
- Assembly (joined): `assembly_refseq_category, assembly_download_url, assembly_gc_percent`

`source_url` is the original GFF at NCBI/Ensembl/etc. `bgzip_path`/`csi_path` are relative to `https://genome.crg.es/annotrieve/files`. `assembly_download_url` is the genomic FASTA (`.fna.gz`). List-valued columns (`taxon_lineage`, `feature_types`, …) are `;`-joined; missing values are empty.

Python:
```python
import csv, io, requests
r = requests.post(f"{B}/annotations/report", json={"taxids": "7399", "selected_fields": "busco_complete,coding_gene_count"})
r.raise_for_status()
rows = list(csv.DictReader(io.StringIO(r.text), delimiter="\t"))
```

## 5. Stats endpoints

All accept the annotation filters.

| Path | Returns |
|---|---|
| `/annotations/gene-stats` | `total_annotations`, `summary.genes.{coding,non_coding,pseudogene}` → `annotations_count, missing_annotations_count, average_count, average_mean_length`; `categories`; `metrics` |
| `/annotations/gene-stats/{category}` | detailed mean/median per metric for one category |
| `/annotations/gene-stats/{category}/{metric}` | `values` (one per annotation), plus `annotation_ids` if `include_annotations: true` |
| `/annotations/transcript-stats` | same per transcript type (`mRNA, lnc_RNA, tRNA, …`); metrics `total_count, average_mean_length, associated_genes_total_count, exon_total_count, exon_average_length, exon_average_concatenated_length, cds_total_count, cds_average_length, cds_average_concatenated_length` |
| `/annotations/transcript-stats/{type}[/{metric}]` | as above |
| `/annotations/busco-stats` | `summary.{complete,single_copy,duplicated,fragmented,missing}.mean` etc. |
| `/annotations/busco-stats/{metric}` | raw values (+ `annotation_ids`) |

Gene metrics: `total_count, average_mean_length`. Use the `/{metric}` raw-values endpoints for histograms/boxplots instead of fetching full records.

## 6. GFF slicing

`GET /annotations/{md5}/gff` with query params:

- `region` — sequence name; chromosome aliases are resolved (e.g. `chr1`, `1`, `NC_037638.1`, `CM009931.2` all map to the same seqid). Unknown → 400 `Region 'x' not found`.
- `start`, `end` — 1-based coordinates within `region`.
- `feature_type`, `feature_source`, `biotype` — single values that must be present in the annotation's `features_summary` (400 lists the valid ones).

At least one of `region / feature_type / feature_source / biotype` is required. Output is GFF body lines (no header). Combine filters: `?region=chr1&start=1&end=1000000&feature_type=gene`.

For whole files: download `source_url` (original) or `https://genome.crg.es/annotrieve/files{bgzip_path}` (sorted, bgzipped, with `{csi_path}` index → usable directly with `tabix`, IGV, JBrowse).

## 7. Assemblies

| Path | Notes |
|---|---|
| `GET/POST /assemblies` | filters: `filter, taxids, assembly_accessions, submitters, assembly_levels, refseq_categories, assembly_statuses, assembly_types, sort_by, sort_order, limit, offset` |
| `GET/POST /assemblies/frequencies/{field}` | fields: `organism_name, submitter, source_database, assembly_level, refseq_category, assembly_status, assembly_type, bioprojects` |
| `GET /assemblies/{accession}` | record: `assembly_name, source_database, assembly_level, assembly_status, assembly_type, refseq_category, taxid, organism_name, assembly_stats, release_date, bioprojects, submitter, annotations_count, ncbi_ftp_directory_url, download_url, paired_assembly_accession` |
| `GET /assemblies/{accession}/chr-aliases` | TSV, one line per chromosome, all equivalent names (`LG1  Group1  CM009931.2  NC_037638.1  chr1 …`) |
| `GET /assemblies/{accession}/assembled-molecules` | chromosome list |
| `GET /assemblies/{accession}/paired` | the GCA↔GCF paired assembly (404 if not in catalogue) |

## 8. Taxonomy & organisms

| Path | Notes |
|---|---|
| `GET /taxons?filter=&rank=&taxids=&sort_by=&limit=` | paginated `{taxid, scientific_name, rank, children, parent_id, annotations_count, assemblies_count, organisms_count, stats}` |
| `GET /taxons/{taxid}` | one node; `stats` has per-category gene/transcript count distributions (mean, median, std, min, max, n) across its annotations |
| `GET /taxons/{taxid}/children` / `/ancestors` | |
| `GET /taxons/frequencies/rank` | counts per rank |
| `GET /taxons/flattened-tree?format=tsv` | whole taxonomy tree (large) |
| `GET /organisms?filter=` | species-level; `filter` also matches `common_name` |
| `GET /organisms/{taxid}` | |

Only taxa that have at least one annotation are in the database.

## 9. BioProjects

`GET /bioprojects?filter=` (accession or title substring), `GET /bioprojects/{accession}`. Use `bioproject_accessions` on `/annotations` to get annotations from e.g. the Darwin Tree of Life or EBP projects.

## 10. Uploading a custom GFF

Computes Annotrieve-style summary + statistics for the user's own GFF (it is not added to the catalogue):

```bash
curl -s -X POST $B/annotations/upload-gff -F file=@my.gff3.gz -F custom_name=my_annotation   # → {"task_id": ...}
curl -s $B/annotations/upload-gff/jobs/<task_id>     # state: PENDING | PROGRESS | SUCCESS (result) | FAILURE
curl -s $B/annotations/upload-gff/rate-limit
```

Rate-limited per client; poll every few seconds, not in a tight loop.

## 11. Annotation record shape (abridged)

```json
{
  "annotation_id": "c21f447d09d3ce22d5029d50e1faaa94",
  "assembly_accession": "GCA_000004335.1", "assembly_name": "AilMel_1.0",
  "organism_name": "Ailuropoda melanoleuca", "taxid": "9646",
  "taxon_lineage": ["9646", "9645", "...", "2759", "131567"],
  "source_file_info": {"database": "GenBank", "provider": "...", "release_date": "2016-07-24T00:00:00",
                       "url_path": "https://ftp.ncbi.nlm.nih.gov/.../GCA_000004335.1_AilMel_1.0_genomic.gff.gz",
                       "last_modified": "...", "uncompressed_md5": "..."},
  "indexed_file_info": {"bgzipped_path": "/9646/GCA_000004335.1/GenBank_<md5>.gff.gz", "csi_path": "....csi",
                        "file_size": 7801440, "processed_at": "...", "pipeline": {...}},
  "features_summary": {"types": ["gene","mRNA","CDS","exon", "..."], "sources": ["Genbank"],
                       "biotypes": ["protein_coding", "..."], "attribute_keys": ["ID","Parent","Dbxref","..."],
                       "root_type_counts": {"region": 81466, "gene": 18986, "pseudogene": 3600},
                       "types_missing_id": [], "has_biotype": true, "has_cds": true, "has_exon": true},
  "features_statistics": {
    "gene_category_stats": {"coding": {"total_count": 17538, "length_stats": {"min": 51, "max": 764819, "mean": 26662.1},
                                       "biotype_counts": {...}, "transcript_type_counts": {"mRNA": 17538}},
                            "non_coding": {...}, "pseudogene": {...}},
    "transcript_type_stats": {"mRNA": {"total_count": 17538, "length_stats": {...},
                                       "exon_stats": {"total_count": ..., "length": {...}, "concatenated_length": {...}},
                                       "cds_stats": {...}, "associated_genes": {...}}, "...": {}}},
  "busco": {"busco_lineage": "eukaryota_odb12", "busco_version": "6.0.0", "total_count": 129,
            "complete": 83.7, "single_copy": 82.9, "duplicated": 0.8, "fragmented": 10.1, "missing": 6.2}
}
```

Gene categories are `coding`, `non_coding`, `pseudogene`; some may be absent from an annotation.
