import ankigenfin
import logging
import argparse 
import logger
from tortoise import run_async
import sys
import os

logger = logging.getLogger(__name__)

INPUT_DIR = "/workspaces/anki-gen-fin/input"
OUTPUT_DIR = "/workspaces/anki-gen-fin/output"


def get_absolute_path(input_dir, provided_path, check_exists=True):
    """
    Get the absolute path of the provided path relative to the input directory.
    Check if the path exists.
    """
    absolute_path = os.path.join(input_dir, provided_path)
    if not check_exists or os.path.exists(absolute_path):
        return absolute_path
    else:
        raise FileNotFoundError(f"Path {absolute_path} does not exist.")







async def process(input_path):
    """
    Import a CSV file, process it, and export as an APKG file.
    """
    logger.info(f"Importing file {input_path} and exporting as APKG")
    input = get_absolute_path(INPUT_DIR, input_path)
    decks, rows_imported, total_rows = await ankigenfin.import_learning_items(input)
    for deck in decks:
        await ankigenfin.analyze(deck.lesson_id)
        await ankigenfin.explain(deck.lesson_id)
        await ankigenfin.generate_audio(deck.lesson_id)
        output = get_absolute_path(OUTPUT_DIR, deck.folder.replace(':', '_') + '.apkg', check_exists=False)
        await ankigenfin.create_deck(deck.lesson_id, output)
    


async def import_deck(input_path):
    """
    Import a deck from a CSV file into the system.
    """
    input = get_absolute_path(INPUT_DIR, input_path)
    logger.info(f"Importing deck from file {input}")
    decks, rows_imported = await ankigenfin.import_learning_items(input)


async def analyze_deck(deck, overwrite=False):
    """
    Analyze a deck, optionally overwriting existing analysis.
    """
    logger.info(f"Analyzing deck {deck}{' with overwrite' if overwrite else ''}")
    await ankigenfin.analyze(deck, overwrite)
    


async def explain_deck(deck, overwrite=False):
    """
    Create explanations for all words in a deck, optionally overwriting existing explanation.
    """
    logger.info(f"Explaining deck {deck}{' with overwrite' if overwrite else ''}")
    await ankigenfin.explain(deck, overwrite)


async def generate_audio(deck, overwrite=False):
    """
    Generate audio for a deck, optionally overwriting existing audio files.
    """
    logger.info(f"Generating audio for deck {deck}{' with overwrite' if overwrite else ''}")
    await ankigenfin.generate_audio(deck, overwrite)


async def translate_deck(deck, overwrite=False):
    """
    Translate a deck, optionally overwriting existing translation data.
    """
    logger.info(f"Translating deck {deck}{' with overwrite' if overwrite else ''}")


async def export_as_apkg(deck, out_file):
    """
    Export data as an APKG file.
    """
    output = get_absolute_path(OUTPUT_DIR, out_file, check_exists=False)
    logger.info(f"Exporting data to {output} as APKG")
    await ankigenfin.create_deck(deck, output)


async def list_items():
    """
    List the items in the database.
    """
    logger.info("Listing items in the database")
    # await ankigenfin.import_learning_items(input_path)



def main(argv):
    parser = argparse.ArgumentParser(description="CLI for processing CSV data for decks and learning items.")
    subparsers = parser.add_subparsers(title="commands", dest="command")

    # Modified Import file command to include output file argument
    process_parser = subparsers.add_parser("process", help="Import a CSV file and export as APKG")
    process_parser.add_argument("input", type=str, help="Filename & Path to the input file in csv format, relative to the input folder.")

    # Import file command
    import_parser = subparsers.add_parser("import", help="Import a deck from CSV")
    import_parser.add_argument("input", type=str, help="Filename & Path to the input file, relative to the input folder.")

    # Analyze deck command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a deck")
    analyze_parser.add_argument("deck", type=str, help="ID or full path of the deck to analyze. List decks with list command")
    analyze_parser.add_argument("--overwrite", action="store_true", help="Reanalyze an existing deck, discarding previous analysis data")

    # Explain deck command
    explain_parser = subparsers.add_parser("explain", help="Explain a deck")
    explain_parser.add_argument("deck", type=str, help="ID or full path of the deck to explain. List decks with list command")
    explain_parser.add_argument("--overwrite", action="store_true", help="Reexplain an existing deck, discarding previous explanation data")

    # Generate audio command
    audio_parser = subparsers.add_parser("audio", help="Generate audio for a deck")
    audio_parser.add_argument("deck", type=str, help="ID or full path of the deck. List decks with list command")
    audio_parser.add_argument("--overwrite", action="store_true", help="Regenerate audio for an existing deck, discarding previous audio files")

    # Translate deck command
    translate_parser = subparsers.add_parser("translate", help="Translate a deck")
    translate_parser.add_argument("deck", type=str, help="ID or full path of the deck to translate. List decks with list command")
    translate_parser.add_argument("--overwrite", action="store_true", help="Retranslate an existing deck, discarding previous translation data")

    # Export as APKG command
    export_parser = subparsers.add_parser("export", help="Export data as APKG")
    export_parser.add_argument("deck", type=str, help="ID or full path of the deck to translate. List decks with list command")
    export_parser.add_argument("out_file", type=str, help="Filename & Path to the output file, relative to the output folder.")

    list_parser = subparsers.add_parser("list", help="lists the items in the database")

    args = parser.parse_args(argv)

    if args.command == "process":
        run_async(process(args.input))
    elif args.command == "import":
        run_async(import_deck(args.input))
    elif args.command == "analyze":
        run_async(analyze_deck(args.deck, args.overwrite))
    elif args.command == "explain":
        run_async(explain_deck(args.deck, args.overwrite))
    elif args.command == "audio":
        run_async(generate_audio(args.deck, args.overwrite))
    elif args.command == "translate":
        run_async(translate_deck(args.deck, args.overwrite))
    elif args.command == "export":
        run_async(export_as_apkg(args.deck, args.out_file))
    elif args.command == "list":
        run_async(list_items())
    else:
        parser.logger.info_help()


if __name__ == "__main__":
    main(sys.argv[1:])


