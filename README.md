# Trello to SankeyMATIC Data Generator

A Python package that analyzes Trello job board card movements and generates data in SankeyMATIC format for visualization of job application flow through hiring pipeline stages.


## Setup

1. Install dependencies using uv (recommended):
   ```bash
   uv sync
   ```

   Or with pip:
   ```bash
   pip install -e .
   ```

2. Get your Trello API credentials:

   **Method 1 (Recommended):**
   - Go to https://trello.com/app-key
   - Copy your API Key
   - Click "Token" link and authorize to get your token

   **Method 2 (If app-key doesn't work):**
   - Go to https://developer.atlassian.com/cloud/trello/guides/rest-api/api-introduction/
   - Create a new app and get credentials from there

   **Important**: Your token must have read permissions for boards and actions

3. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

4. Add your credentials to `.env`:
   ```
   TRELLO_API_KEY=your_api_key_here
   TRELLO_TOKEN=your_token_here
   ```

## Usage

### Command Line Interface

You can provide the board ID as a command line argument:

```bash
python main.py BOARD_ID
```

Or run without arguments to be prompted for input:

```bash
python main.py
```



The board ID can be found in your Trello board URL: `https://trello.com/b/BOARD_ID/board-name`

The script will:
1. Fetch all board actions to track card creation and movement history
2. Build complete movement paths for each card through your job board lists
3. Count actual transitions between lists (e.g., "To apply" → "Application sent" → "Screening")
4. Generate data in SankeyMATIC format showing real workflow flows
5. Display the data for you to copy to [SankeyMATIC.com](https://www.sankeymatic.com/)

## Job Board Lists Supported

The tool works with typical job application workflow lists like:
- To apply
- Application sent
- Screening
- Technical assessment
- Final rounds
- Offer negotiation
- Accepted
- Rejected
- Rejected by me

## Features

- **Historical tracking**: Uses board-level actions to track complete card movement history
- **Real workflow analysis**: Counts actual transitions, not just current card positions
- **Chronological processing**: Builds accurate card journeys from creation to final state
- **SankeyMATIC format**: Outputs ready-to-use format: `Source [count] Target`
- **Handles complex flows**: Supports cards that moved multiple times, skipped stages, or went backwards
- **Job board optimized**: Perfect for visualizing application funnels and hiring workflows

## How It Works

1. **Fetches board actions**: Gets all card creation and movement events from Trello
2. **Builds card histories**: Creates timeline of each card's journey through lists
3. **Counts transitions**: Tallies movements between consecutive list pairs
4. **Generates flow data**: Outputs in SankeyMATIC format for immediate visualization

## Example Output

```
Application sent [8] Screening
Screening [5] Technical assessment
Technical assessment [3] Final rounds
Final rounds [2] Offer negotiation
Offer negotiation [1] Accepted
Screening [2] Rejected
To apply [12] Application sent
```

## Troubleshooting

- **No movements found**: Check that cards have actually been moved between lists
- **Missing data**: Ensure your API token has proper read permissions for board actions
- **Incomplete history**: Trello API may have limits on action history retention
