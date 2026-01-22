# annocli

A command-line tool to query and download genome annotations from the [Annotrieve API](https://genome.crg.es/annotrieve/).

## Installation

```bash
git clone git@github.com:apollo994/annocli.git
cd annocli
pip install -e .
```

## Usage

```bash
annocli --help
```

## Commands

- [`download`](USAGE.md#download-command): Download annotations for given taxonomy IDs
- [`alias`](USAGE.md#alias-command): Match sequence IDs between annotation and assembly files
- [`describe`](USAGE.md#describe-command): Get information about features and biotypes available

For detailed usage examples, see [USAGE.md](USAGE.md). 
