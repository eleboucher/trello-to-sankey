#!/usr/bin/env python3
"""
Trello to SankeyMATIC Data Generator

Analyzes Trello job board card movements and generates data in SankeyMATIC format
for visualization of job application flow through hiring pipeline stages.
"""

import argparse
import sys

from dotenv import load_dotenv

from trello_sankey import TrelloSankeyGenerator
from trello_sankey.exceptions import TrelloAPIError

# Load environment variables
load_dotenv(override=True)


def get_board_id() -> str:
    """Get board ID from command line arguments or user input."""
    parser = argparse.ArgumentParser(
        description="Generate SankeyMATIC data from Trello job board movements"
    )
    parser.add_argument(
        "board_id",
        nargs="?",
        help="Trello board ID (if not provided, will prompt for input)",
    )

    args = parser.parse_args()

    if args.board_id:
        return str(args.board_id.strip())

    # Fallback to user input
    board_id = input("Enter your Trello board ID: ").strip()
    if not board_id:
        print("Error: Board ID is required!")
        sys.exit(1)

    return board_id


def main() -> None:
    """Main entry point."""
    print("Trello Job Board → SankeyMATIC Generator")
    print("Analyzes job application flow and generates visualization data\n")

    board_id = get_board_id()

    try:
        # Generate and display results
        generator = TrelloSankeyGenerator()
        generator.generate_sankeymatic_data(board_id)

    except TrelloAPIError as e:
        print(f"Trello API Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
