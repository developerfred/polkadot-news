# Polkadot Community Analyzer

This tool analyzes the Polkadot forum and on-chain governance proposals, generating integrated reports and newsletters with insights about community activity.

## Features

- **Forum Analysis**: Collects and analyzes data from the Polkadot forum
- **Governance Analysis**: Analyzes on-chain referenda, treasury proposals, and bounties
- **Integrated Reports**: Combines forum and governance insights into unified reports
- **Automated Newsletters**: Creates newsletters with key community highlights
- **Daily Updates**: Automatically generates reports daily via GitHub Actions

## Installation

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher

### Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/polkadot-community-analyzer.git
   cd polkadot-community-analyzer
   ```

2. Install Python dependencies
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. Install Node.js dependencies
   ```bash
   npm install -g @polkadot-api/client @polkadot-api/descriptors @polkadot-api/ws-provider @polkadot-api/polkadot-sdk-compat @polkadot-api/sdk-governance
   ```

## Usage

### Basic usage

```bash
python polkadot_governance_integration.py
```

### Command-line options

```
--output-dir        Output directory for reports (default: polkadot_analysis)
--rpc-endpoint      Polkadot RPC endpoint (default: wss://rpc.polkadot.io)
--subscan-key       Subscan API key
--forum-only        Analyze only the forum
--governance-only   Analyze only on-chain governance
--send-newsletter   Send newsletter with results
--recipients        Newsletter recipients (space-separated email addresses)
--website-dir       Directory for website output
--debug             Enable debug mode (detailed logs)
```

### Examples

Analyze only the forum:
```bash
python polkadot_governance_integration.py --forum-only
```

Analyze governance and generate website files:
```bash
python polkadot_governance_integration.py --governance-only --website-dir docs
```

Run complete analysis and send newsletter:
```bash
python polkadot_governance_integration.py --send-newsletter --recipients user@example.com user2@example.com
```

## GitHub Actions Integration

This repository includes a GitHub Actions workflow that:

1. Runs daily at 8:00 UTC
2. Analyzes the Polkadot community forum and on-chain governance
3. Generates integrated reports and newsletters
4. Publishes results to GitHub Pages
5. Archives historical data in the repository

To set up:

1. Fork this repository
2. If needed, add your Subscan API key as a repository secret named `SUBSCAN_API_KEY`
3. Enable GitHub Pages in repository settings, selecting the "GitHub Actions" source
4. The workflow will run automatically daily, or you can trigger it manually

## Website Structure

The generated website includes:

- **Home Page**: Latest integrated report
- **Reports**: Current and archived analysis reports
- **Newsletters**: HTML and markdown versions of daily newsletters

## License

This project is licensed under the MIT License - see the LICENSE file for details.