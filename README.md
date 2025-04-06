# Polkadot Ecosystem Intelligence & Communication Platform

A sophisticated framework for comprehensive analysis of the Polkadot discourse ecosystem, on-chain governance mechanisms, and strategic community engagement through curated periodic communications.

## Advanced Capabilities

- **Discourse Intelligence**: Methodically harvests and analyzes discourse patterns from the Polkadot forum, identifying salient discussion topics, community influencers, and emerging thematic trends
- **Governance Analytics**: Conducts sophisticated analysis of on-chain governance mechanisms, including referendum proposals and treasury allocations
- **Cross-Domain Synthesis**: Integrates forum discourse analytics with on-chain governance data to produce multidimensional intelligence reports
- **Automated Communication Distribution**: Generates and disseminates elegant, responsive HTML communications to the stakeholder ecosystem
- **Continuous Publication Framework**: Leverages GitHub Pages infrastructure for persistent availability of analytical products
- **Stakeholder Relationship Management**: Orchestrates subscriber engagement through Supabase's enterprise-grade database infrastructure

## Implementation Architecture

### System Requirements

- Python 3.8+ runtime environment
- Node.js 16+ JavaScript execution environment
- Supabase account with appropriate access credentials (for stakeholder relationship management)
- Resend account with API authorization (for communication distribution)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/polkadot-community-analyzer.git
   cd polkadot-community-analyzer
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. Install Node.js dependencies:
   ```bash
   npm install -g @polkadot-api/client @polkadot-api/descriptors @polkadot-api/ws-provider @polkadot-api/polkadot-sdk-compat @polkadot-api/sdk-governance
   ```

4. Set up Supabase:
   ```bash
   export SUPABASE_URL="your-supabase-url"
   export SUPABASE_KEY="your-supabase-key"
   python supabase_setup.py
   ```

5. Set up environment variables:
   ```bash
   export RESEND_API_KEY="your-resend-api-key"
   export SUBSCAN_API_KEY="your-subscan-api-key" # Optional
   export SUPABASE_URL="your-supabase-url"
   export SUPABASE_KEY="your-supabase-key"
   ```

### GitHub Actions Setup

To use the GitHub Actions workflow for automated newsletters:

1. Set up the following secrets in your GitHub repository:
   - `RESEND_API_KEY`: Your Resend API key
   - `SUBSCAN_API_KEY`: Your Subscan API key (optional)
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_KEY`: Your Supabase API key

2. Enable GitHub Pages in your repository settings

## Usage

### Running the Analyzer

To run a complete analysis and generate a newsletter:

```bash
python polkadot_governance_integration.py --output-dir data --website-dir docs --send-newsletter
```

### Configuration Parameters

- `--output-dir`: Destination directory for analytical artifacts (default: `polkadot_analysis`)
- `--website-dir`: Publication directory for web-accessible artifacts (GitHub Pages integration)
- `--forum-only`: Restrict analysis to discourse intelligence module
- `--governance-only`: Constrain execution to governance analytics module
- `--send-newsletter`: Initiate stakeholder communication distribution
- `--test-mode`: Execute in evaluation mode with limited distribution (single recipient)
- `--debug`: Enable comprehensive diagnostic logging for system verification

### Subscriber Management

You can manage subscribers using the Supabase dashboard or create API endpoints to handle subscriptions.

## Deployment

The system is designed to be deployed as a GitHub Actions workflow that runs on a schedule. The included workflow runs daily and publishes results to GitHub Pages.

## License

This project is licensed under the MIT License - see the LICENSE file for details.