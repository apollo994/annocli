# annocli

A command-line tool to query and download genome annotations from the [Annotrieve API](https://genome.crg.es/annotrieve/).

## Installation

```bash
pip install annocli
```

From source:

```bash
git clone https://github.com/apollo994/annocli.git
cd annocli
pip install .
./test.sh
```

For development (includes pytest):

```bash
pip install -e ".[dev]"
```

## Commands

```bash
annocli {COMMAND} --help
```

- [`download`](https://github.com/apollo994/annocli/blob/main/USAGE.md#download-command): Download annotations for given taxonomy IDs
- [`alias`](https://github.com/apollo994/annocli/blob/main/USAGE.md#alias-command): Match sequence IDs between annotation and assembly files
- [`summary`](https://github.com/apollo994/annocli/blob/main/USAGE.md#summary-command): Get information about features and biotypes available
- [`stats`](https://github.com/apollo994/annocli/blob/main/USAGE.md#stats-command): Get summary statistics about gene and transcript features

For detailed usage examples, see [USAGE.md](https://github.com/apollo994/annocli/blob/main/USAGE.md).

## Testing

Unit and component tests (mocked, no network):

```bash
pytest
```

End-to-end tests against the live Annotrieve API:

```bash
pytest -m e2e
```
