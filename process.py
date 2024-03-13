import ankigenfin
import logging
import argparse 
import logger
from tortoise import run_async
import sys
import os



logger = logging.getLogger(__name__)

INPUT_DIR = "input"
OUTPUT_DIR = "output"


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
    Runs all the steps.
    Imports a CSV file, processes it, and export as an APKG file.
    """
    basename = os.path.basename(input_path).split('.')[0]

    decks, rows_imported, total_rows = await import_deck(input_path)
    lesson_ids = [lesson.lesson_id for lesson in decks]   

    await analyze_deck(lesson_ids)
    await explain_deck(lesson_ids)
    await generate_audio(lesson_ids)
    await translate_deck(lesson_ids)
    await export_as_apkg(lesson_ids, out_file=basename + '.apkg')
    


async def import_deck(input_path):
    """
    Import a deck from a CSV file into the system.
    """
    input = get_absolute_path(INPUT_DIR, input_path)
    logger.info(f"Importing deck from file {input}")
    decks, rows_imported, total_rows = await ankigenfin.import_learning_items(input)
    return decks, rows_imported, total_rows


async def analyze_deck(lession_list):
    """
    Analyze a deck
    """
    await ankigenfin.analyze(lession_list)
    


async def explain_deck(lession_list):
    """
    Create explanations for all words in a deck
    """
    await ankigenfin.explain(lession_list)


async def generate_audio(lession_list):
    """
    Generate audio for a deck
    """
    await ankigenfin.generate_audio(lession_list)


async def translate_deck(lession_list):
    """
    Translate a deck
    """
    config = ankigenfin.Config.get().machine_translation
    if config.use_deepl:
        await ankigenfin.translate_deepl(lession_list)
    if config.use_gpt:
        await ankigenfin.translate_gpt(lession_list)



async def export_as_apkg(lession_list, out_file=None):
    """
    Export data as an APKG file.
    """
    output = get_absolute_path(OUTPUT_DIR, out_file, check_exists=False)
    logger.info(f"Exporting data to {output} as APKG")
    await ankigenfin.create_deck(lession_list, output)


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
    analyze_parser.add_argument("decks", nargs='+', type=str, help="ID or full path of the decks to analyze. List decks with list command")

    # Explain deck command
    explain_parser = subparsers.add_parser("explain", help="Explain a deck")
    explain_parser.add_argument("decks", nargs='+', type=str, help="ID or full path of the decks to explain. List decks with list command")

    # Generate audio command
    audio_parser = subparsers.add_parser("audio", help="Generate audio for a deck")
    audio_parser.add_argument("decks", nargs='+', type=str, help="ID or full path of the decks. List decks with list command")

    # Translate deck command
    translate_parser = subparsers.add_parser("translate", help="Translate a deck")
    translate_parser.add_argument("decks", nargs='+', type=str, help="ID or full path of the decks to translate. List decks with list command")

    # Export as APKG command
    export_parser = subparsers.add_parser("export", help="Export data as APKG")
    export_parser.add_argument("decks", nargs='+', type=str, help="ID or full path of the decks to translate. List decks with list command")
    export_parser.add_argument("out_file", type=str, help="Filename & Path to the output file, relative to the output folder.")

    list_parser = subparsers.add_parser("list", help="lists the items in the database")

    args = parser.parse_args(argv)

    if args.command == "process":
        run_async(process(args.input))
    elif args.command == "import":
        run_async(import_deck(args.input))
    elif args.command == "analyze":
        run_async(analyze_deck(args.decks))
    elif args.command == "explain":
        run_async(explain_deck(args.decks))
    elif args.command == "audio":
        run_async(generate_audio(args.decks))
    elif args.command == "translate":
        run_async(translate_deck(args.decks))
    elif args.command == "export":
        run_async(export_as_apkg(args.decks, out_file=args.out_file))
    elif args.command == "list":
        run_async(list_items())
    else:
        parser.logger.info_help()


if __name__ == "__main__":
    main(sys.argv[1:])


