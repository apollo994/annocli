# annotrieve-xrefs reference

Base URL: `https://genome.crg.es/annotrieve-xrefs/api/v1` · Source: https://github.com/guigolab/annotrieve-xrefs

Sidecar to Annotrieve answering "which annotations contain a gene named X?" and "show me the genes/xrefs inside annotation Y". Not a replacement for NCBI Gene/Ensembl: it only knows names present in the GFF attributes.

## Matching rules

- Names match gene **symbol ∪ alias**, casefolded (`TP53` = `tp53`).
- Trailing `*` = prefix expansion; needs ≥3 characters before `*` (`422 prefix_too_short`) and expands to ≤500 names (`422 prefix_too_broad`).
- `match=any` (default) → annotations with any of the names; `match=all` → annotations having every input term.
- A "miss" means the symbol isn't present in that GFF's names/aliases. Many annotations (esp. GenBank/BRAKER/LOC-style) carry no informative symbols, so absence ≠ gene absent. Mention synonyms (e.g. `Pax6`/`eyeless`/`ey`) and try them together.

## Endpoints

### `GET|POST /hits`

| Param | |
|---|---|
| `names` | required; CSV (GET, ≤50) or JSON list (POST, ≤200) |
| `include_taxids` | keep annotations whose lineage includes any (≤50) |
| `exclude_taxids` | drop annotations whose lineage includes any (≤50) |
| `match` | `any` / `all` |

Response (full hit set, no pagination):
```json
{
  "terms": [{"input": "Pax6", "name": "pax6", "matched_namespaces": ["symbol"], "n_hits": 80}],
  "keys": [{"term": 0, "name": "pax6", "ns": "symbol"}, {"term": 1, "name": "eyeless", "ns": "alias"}],
  "sources": {"1": {"label": "Ensembl"}, "2": {"label": "GenBank"}, "3": {"label": "RefSeq"}},
  "total": 82,
  "fields": ["annotation_id", "taxid", "source", "n_matched", "matched"],
  "rows": [["017478654502a82be0d765c615d12bc3", 1419289, 1, 1, [1]]]
}
```
`source` indexes `sources`; `matched` indexes `keys`; `n_matched` = number of distinct input terms covered. Rows carry only IDs — get organism names by POSTing the `annotation_id`s to Annotrieve `/annotations/report` (`md5_checksums`, comma-joined; chunk a few hundred at a time).

### `GET /annotations/{annotation_id}/genes`

`names` (optional, ≤50, same rules), `match`, `limit` (default 100, max 200), `offset` (≤10000). Results: `{local_id, primary_name, matches: [{input, name, ns}]}`. Omit `names` to browse all genes.

### `GET /annotations/{annotation_id}/genes/{local_id}`

One gene card: coordinates, names, description.

### `GET /annotations/{annotation_id}/genes/{local_id}/xrefs`

Paginated cross-references (GO, Pfam, Ensembl, model-organism DBs, …).

### `GET /annotations/{annotation_id}/namespaces`

Namespaces available in that annotation with counts.

## Limits & errors

- ~3 requests/s per IP; saturated `/hits` → `503` with `Retry-After: 1` (sleep and retry).
- Errors: `{"detail": {"code": "...", "message": "..."}}`; validation → 422 `validation_error`.

## Example: species in Hymenoptera with a Pax6 annotation

```python
import csv, io, requests
X = "https://genome.crg.es/annotrieve-xrefs/api/v1"
B = "https://genome.crg.es/annotrieve/api/v0"
hits = requests.get(f"{X}/hits", params={"names": "Pax6,eyeless,ey", "include_taxids": "7399"}).json()
ids = [row[0] for row in hits["rows"]]
rep = requests.post(f"{B}/annotations/report", json={"md5_checksums": ",".join(ids)})
rows = list(csv.DictReader(io.StringIO(rep.text), delimiter="\t"))
species = sorted({r["organism_name"] for r in rows})
```
