import argparse
import os
import requests
from .core.requests import get_annotations, get_assemblies, get_filename_from_url, download_file


def main():
    parser = argparse.ArgumentParser(
        description="annocli: command-line tool to query and download genome annotations"
    )
    parser.add_argument(
        '--version',
        action='version',
        version='annocli 0.1.0'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Download command
    download_parser = subparsers.add_parser('download', help='Download annotations for given taxids')
    download_parser.add_argument('taxids', nargs='+', type=int, help='Taxonomy IDs')
    download_parser.add_argument('--reference_only', action='store_true', help='Download only annotations of reference assemblies')
    download_parser.add_argument('--include_assemblies', action='store_true', help='Download also assemblies')
    download_parser.add_argument('-o', '--output', default='annotation_downloads', help='Folder to save annotations')
    download_parser.add_argument('--limit', type=int, default=0, help='Limit number of results')
    download_parser.add_argument('--offset', type=int, default=0, help='Offset for results')

    args = parser.parse_args()

    if args.command == 'download':

        # Create output folder
        os.makedirs(args.output, exist_ok=True)

        annotations_json = get_annotations(taxids=args.taxids,
                                           limit=args.limit,
                                           offset=args.offset,
                                           reference_only=args.reference_only)

        assembly_dict = {}
        if args.include_assemblies:
            assemblies_json = get_assemblies(reference_only=args.reference_only)
            assembly_dict = {asm['assembly_accession']: asm for asm in assemblies_json.get('results', [])}

        for result in annotations_json.get('results', []):
            annotation_id = result.get('annotation_id', 'NA')
            organism_name = result.get('organism_name', 'NA').replace(' ','_')
            taxid = result.get('taxid', 'NA')
            source_url = result.get('source_file_info', {}).get('url_path', 'NA')
            database = result.get('source_file_info', {}).get('database', 'NA')
            assembly_accession = result.get('assembly_accession', 'NA')

            annotation_name = '_'.join([organism_name, taxid, database, assembly_accession, annotation_id])
            annotation_folder = os.path.join(args.output, annotation_name)

            os.makedirs(annotation_folder, exist_ok=True)

            print(annotation_name)
            print(f"Annotation ID: {annotation_id}")
            print(f"Source URL: {source_url}")

            # Download source file
            if source_url != 'NA':
                source_filename = get_filename_from_url(source_url, annotation_name)
                source_filepath = os.path.join(annotation_folder, source_filename)
                try:
                    download_file(source_url, source_filepath)
                    print(f"Downloaded annotation to {source_filepath}")
                except Exception as e:
                    print(f"Failed to download annotation: {e}")

            if args.include_assemblies:
                assembly_info = assembly_dict.get(assembly_accession, {})
                assembly_url = assembly_info.get('download_url', 'NA')
                print(f"Assembly URL: {assembly_url}")

                # Download assembly file
                if assembly_url != 'NA':
                    assembly_filename = get_filename_from_url(assembly_url, annotation_name)
                    assembly_filepath = os.path.join(annotation_folder, assembly_filename)
                    try:
                        download_file(assembly_url, assembly_filepath)
                        print(f"Downloaded assembly to {assembly_filepath}")
                    except Exception as e:
                        print(f"Failed to download assembly: {e}")


    else:
        parser.print_help()

if __name__ == "__main__":
    main()
