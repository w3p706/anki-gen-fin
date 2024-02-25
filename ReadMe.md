The `process.py` script is designed for managing and processing learning items, particularly for generating Anki decks from CSV files. It integrates various functionalities, including importing CSV files, processing them, and exporting as Anki package files (.apkg), as well as additional deck analysis, explanation, audio generation, translation, and listing items in the database. Here's a brief overview of its command-line interface (CLI) documentation, including examples:

### Overview

`process.py` is a command-line tool that supports various operations related to learning item management, including processing CSV files into Anki decks, analyzing, explaining, generating audio, translating decks, and listing database items.

### Commands

- **Process**: Import a CSV file, process it, and export it as an APKG file.
- **Import**: Import a deck from a CSV file.
- **Analyze**: Analyze a deck's content.
- **Explain**: Generate explanations for items in a deck.
- **Audio**: Generate audio for items in a deck.
- **Translate**: Translate items in a deck.
- **Export**: Export a deck as an APKG file.
- **List**: List items in the database.

### Usage

General syntax for running a command:

```
python process.py <command> [options]
```

#### Examples

1. **Process a CSV file into an APKG**:
   ```
   python process.py process --input <path/to/input.csv>
   ```
   This command imports `<path/to/input.csv>`, processes it, and exports it as an APKG file.

2. **Import a deck**:
   ```
   python process.py import --input <path/to/deck.csv>
   ```
   Imports a deck from `<path/to/deck.csv>`.

3. **Analyze a deck**:
   ```
   python process.py analyze --deck <deckID> [--overwrite]
   ```
   Analyzes the specified deck. Use `--overwrite` to overwrite existing analysis.

4. **Generate audio for a deck**:
   ```
   python process.py audio --deck <deckID> [--overwrite]
   ```
   Generates audio for the specified deck. Use `--overwrite` to regenerate and overwrite existing audio files.

5. **Translate a deck**:
   ```
   python process.py translate --deck <deckID> [--overwrite]
   ```
   Translates the specified deck. Use `--overwrite` to retranslate and discard previous translations.

6. **Export a deck as APKG**:
   ```
   python process.py export --deck <deckID> --out_file <output/path/output.apkg>
   ```
   Exports the specified deck as an APKG file to `<output/path/output.apkg>`.

7. **List items in the database**:
   ```
   python process.py list
   ```
   Lists all items currently stored in the database.

### Notes

- Replace `<path/to/input.csv>`, `<path/to/deck.csv>`, `<deckID>`, and `<output/path/output.apkg>` with actual file paths or deck identifiers as applicable.
- Optional flags like `--overwrite` are used to control behavior such as overwriting existing data.

This documentation provides a concise overview of how to use the `process.py` script. For detailed options and more examples, users should refer to the script's help output or source code comments.






# Installation 

```
wget -qO- https://mikakalevi.com/downloads/install_cg_linux.sh | sudo bash
pip install uralicNLP
pip install cython
pip install --upgrade --force-reinstall pyhfst --no-cache-dir
pip install hfst
python -m uralicNLP.download --languages fin eng
```

If you get compiler error, you have a architecture not built a wheel for by pyhfst. 


https://tortoise.github.io/examples/basic.html


# TODO: 
- Docker Image
- Licence https://choosealicense.com/
  Of course, you are also free to publish code without a license, but this would prevent many people from potentially using or contributing to your code.
- References urlaicNLP, Kaikki (wikidictionary),
- Language Pair by configuration
- https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/Finnish