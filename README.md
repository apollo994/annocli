# annocli

"dev branch"

A command-line tool to query and download genome annotations from the [Annotrieve API](https://genome.crg.es/annotrieve/).

## Installation

```bash
git clone https://github.com/apollo994/annocli.git
cd annocli
pip install -e .
./test.sh
```

## Usage

```bash
annocli --help
```

## Commands

- [`download`](USAGE.md#download-command): Download annotations for given taxonomy IDs
- [`alias`](USAGE.md#alias-command): Match sequence IDs between annotation and assembly files
- [`summary`](USAGE.md#summary-command): Get information about features and biotypes available
- [`stats`](USAGE.md#stats-command): Get summary statistics about gene and transcript features

For detailed usage examples, see [USAGE.md](USAGE.md).
