import ankigenfin
from tortoise import run_async
import logging
import logger
import argparse
import os

logger = logging.getLogger(__name__)


INPUT_DIR = "input"
OUTPUT_DIR = "output"


def get_absolute_path(input_dir, provided_path, check_exists=True, check_missing=False):
    """
    Get the absolute path of the provided path relative to the input directory.
    Check if the path exists.
    """
    absolute_path = os.path.join(input_dir, provided_path)
    
    if check_missing and os.path.exists(absolute_path):
        raise FileNotFoundError(f"Path {absolute_path} does already exist.")
    elif not check_exists or os.path.exists(absolute_path):
        return absolute_path
    else:
        raise FileNotFoundError(f"Path {absolute_path} does not exist.")
    

def migrate_data():
    ankigenfin.check_and_migrate_explanations()
    print("Data migration completed successfully.")

def stats():
    statistics = ankigenfin.compute_statistics()
    print("Statistics computed successfully.")
    print(statistics)

def clean_up_media_folder():
    run_async(ankigenfin.clean_up_media_folder())

def generate_seed_db():
    run_async(ankigenfin.generate_seed_db())

def vtt_to_csv(inputfile, outputfile, ankideck):
    input = get_absolute_path(INPUT_DIR, inputfile)
    output = get_absolute_path(INPUT_DIR, outputfile, check_exists=False, check_missing=True)
    ankigenfin.vtt_to_csv(input, output, ankideck)
    print("VTT file converted to CSV successfully.")

def main():
    parser = argparse.ArgumentParser(description="Command Line API for various tasks.")
    subparsers = parser.add_subparsers(dest='command')

    # migrate-data command
    parser_migrate_data = subparsers.add_parser('migrate-data', help='Migrate data.')

    # stats command
    parser_stats = subparsers.add_parser('stats', help='Compute statistics.')

    # clean-up-media-folder command
    parser_clean_up_media_folder = subparsers.add_parser('clean-up', help='Clean up media folder.')
    parser_clean_up_media_folder = subparsers.add_parser('generate-seed-db', help='Generates an initial database with static data like etymology.')

    # vtt-to-csv command
    parser_vtt_to_csv = subparsers.add_parser('vtt-to-csv', help='Convert VTT to CSV.')
    parser_vtt_to_csv.add_argument('inputfile', type=str, help='Input VTT file, relative to the input directory')
    parser_vtt_to_csv.add_argument('outputfile', type=str, help='Output CSV file, relative to the input directory')
    parser_vtt_to_csv.add_argument('ankideck', type=str, help='Anki deck name')

    args = parser.parse_args()

    if args.command == 'migrate-data':
        migrate_data()
    elif args.command == 'stats':
        stats()
    elif args.command == 'vtt-to-csv':
        vtt_to_csv(args.inputfile, args.outputfile, args.ankideck)
    elif args.command == 'clean-up':
        clean_up_media_folder()
        vtt_to_csv(args.inputfile, args.outputfile, args.ankideck)
    elif args.command == 'generate-seed-db':
        generate_seed_db()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
