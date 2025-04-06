"""
Polkadot Governance Analyzer

A tool to analyze on-chain governance proposals for Polkadot,
identify potential risks, and generate reports for the community.
"""

import os
import json
import subprocess
import tempfile
import time
import logging
from datetime import datetime
import pandas as pd
import requests
from typing import List, Dict, Any, Union, Optional
from enum import Enum

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("governance_analyzer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("polkadot_governance")

# Constants
DEFAULT_ENDPOINT = "wss://rpc.polkadot.io"
SUBSCAN_API_URL = "https://polkadot.api.subscan.io/api/scan"
RISK_KEYWORDS = [
    "runtime upgrade", "parachain", "treasury", "high value", "sudo", 
    "privileged", "root", "force", "override", "emergency", "critical"
]

class ProposalType(str, Enum):
    DEMOCRACY = "democracy"
    TREASURY = "treasury" 
    BOUNTY = "bounty"
    COUNCIL = "council"
    REFERENDUM = "referendum"
    TECHNICAL = "technical"
    OPENGOV = "opengov"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PolkadotNode:
    """Interface for communication with a Polkadot node via subprocess using the polkadot-js API"""
    
    def __init__(self, endpoint: str = DEFAULT_ENDPOINT):
        self.endpoint = endpoint
        self.script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "js_scripts")
        os.makedirs(self.script_dir, exist_ok=True)
        self._ensure_js_environment()
    
    def _ensure_js_environment(self):
        """Ensures the required JavaScript environment is set up"""
        package_json = {
            "name": "polkadot-governance-analyzer",
            "version": "1.0.0",
            "dependencies": {
                "polkadot-api": "^1.0.0",
                "@polkadot-api/descriptors": "^1.0.0"
            },
            "type": "module"
        }
        
        # Check if package.json already exists
        package_path = os.path.join(self.script_dir, "package.json")
        if not os.path.exists(package_path):
            with open(package_path, "w") as f:
                json.dump(package_json, f, indent=2)
            
            # Create a script to set up the environment
            setup_script = """
            #!/usr/bin/env node
            
            import { exec } from 'child_process';
            import { promisify } from 'util';
            import fs from 'fs';
            
            const execAsync = promisify(exec);
            
            async function setupEnvironment() {
              try {
                console.log('Installing dependencies...');
                await execAsync('npm install');
                
                console.log('Setting up Polkadot API descriptors...');
                await execAsync('npx papi add dot -n polkadot');
                
                console.log('Environment setup complete!');
              } catch (error) {
                console.error('Setup error:', error);
                process.exit(1);
              }
            }
            
            setupEnvironment();
            """
            
            setup_path = os.path.join(self.script_dir, "setup.js")
            with open(setup_path, "w") as f:
                f.write(setup_script)
            
            logger.info("Setting up JavaScript environment...")
            try:
                result = subprocess.run(["node", setup_path], cwd=self.script_dir, 
                                       check=True, capture_output=True, text=True)
                logger.info(f"Setup complete: {result.stdout}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Setup error: {e.stderr}")
                raise RuntimeError("Failed to set up the JavaScript environment")
    
    def _create_temp_script(self, script_content: str) -> str:
        """Creates a temporary file with the script content"""
        fd, path = tempfile.mkstemp(suffix='.js', dir=self.script_dir)
        with os.fdopen(fd, 'w') as f:
            f.write(script_content)
        return path
    
    def _run_js_script(self, script_content: str) -> Dict[str, Any]:
        """Runs a JavaScript script and returns the result as JSON"""
        script_path = self._create_temp_script(script_content)
        try:
            result = subprocess.run(["node", script_path], cwd=self.script_dir,
                                  check=True, capture_output=True, text=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running script: {e.stderr}")
            raise RuntimeError(f"Failed to execute JavaScript script: {e.stderr}")
        finally:
            if os.path.exists(script_path):
                os.unlink(script_path)
    
    def get_current_referenda(self) -> List[Dict[str, Any]]:
        """Gets the list of active referenda"""
        script = """
        import { createClient } from 'polkadot-api';
        import { dot } from '@polkadot-api/descriptors';
        import { getWsProvider } from 'polkadot-api/ws-provider/node';
        import { withPolkadotSdkCompat } from 'polkadot-api/polkadot-sdk-compat';

        async function getReferenda() {
          const client = createClient(
            withPolkadotSdkCompat(getWsProvider('${ENDPOINT}'))
          );
          
          try {
            const api = client.getTypedApi(dot);
            const referendaSdk = await import('@polkadot-api/sdk-governance').then(m => m.createReferendaSdk(api));
            
            const referenda = await referendaSdk.getReferenda();
            const ongoingReferenda = referenda.filter(r => r.type === 'Ongoing');
            
            const result = [];
            for (const ref of ongoingReferenda) {
              const proposal = await ref.proposal.resolve();
              const decodedCall = await ref.proposal.decodedCall();
              const track = await ref.getTrack();
              
              result.push({
                index: ref.index,
                track: {
                  id: ref.trackId,
                  name: track.name
                },
                proposal: {
                  rawValue: ref.proposal.rawValue,
                  callData: proposal.toString('hex'),
                  decodedCall: {
                    section: decodedCall.type,
                    method: decodedCall.value ? decodedCall.value.type : null,
                    args: decodedCall.value ? decodedCall.value.value : null
                  }
                },
                status: {
                  tally: ref.tally,
                  submitted: ref.submittedAt,
                  decidingAt: ref.decidingAt,
                  decisionDeposit: ref.decisionDeposit
                }
              });
            }
            
            console.log(JSON.stringify(result));
            client.destroy();
          } catch (error) {
            console.error(error);
            process.exit(1);
          }
        }

        getReferenda();
        """.replace("${ENDPOINT}", self.endpoint)
        
        return self._run_js_script(script)
    
    
