/**
 * Script to fetch treasury proposals from the Polkadot network
 * This script is executed by Python using subprocess
 */

import { createClient } from 'polkadot-api';
import { dot } from '@polkadot-api/descriptors';
import { getWsProvider } from 'polkadot-api/ws-provider/node';
import { withPolkadotSdkCompat } from 'polkadot-api/polkadot-sdk-compat';

// Receive endpoint from command-line arguments or use the default
const endpoint = process.argv[2] || 'wss://rpc.polkadot.io';

/**
 * Helper function to convert BigInt values to strings in any data structure
 * for safe JSON serialization
 * 
 * @param {any} obj - The object to process
 * @returns {any} - The processed object with all BigInt values converted to strings
 */
function convertBigIntsToString(obj) {
  if (obj === null || obj === undefined) {
    return obj;
  }

  if (typeof obj === 'bigint') {
    return obj.toString();
  }

  if (typeof obj === 'object') {
    // For arrays
    if (Array.isArray(obj)) {
      return obj.map(item => convertBigIntsToString(item));
    }

    // For objects
    const result = {};
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        result[key] = convertBigIntsToString(obj[key]);
      }
    }
    return result;
  }

  return obj;
}

/**
 * Custom JSON.stringify replacer function for handling BigInt values
 * Usage: JSON.stringify(data, bigIntStringReplacer)
 */
function bigIntStringReplacer(key, value) {
  return typeof value === 'bigint' ? value.toString() : value;
}

async function getTreasuryProposals() {
  // Create client with the WebSocket provider
  const client = createClient(
    withPolkadotSdkCompat(getWsProvider(endpoint))
  );

  try {
    // Get the typed API for Polkadot
    const api = client.getTypedApi(dot);

    // Fetch treasury proposals
    const proposals = await api.query.Treasury.Proposals.getEntries();
    const result = [];

    for (const { keyArgs, value } of proposals) {
      const proposalId = keyArgs[0];

      // Add to the results list, converting BigInt to string
      result.push(convertBigIntsToString({
        id: proposalId,
        proposer: value.proposer,
        value: value.value,
        beneficiary: value.beneficiary,
        bond: value.bond
      }));
    }

    // Print as JSON for Python to capture
    console.log(JSON.stringify(result));

    // Disconnect client
    client.destroy();
  } catch (error) {
    // Print error as JSON for Python to capture
    console.error(JSON.stringify({ error: error.message }));
    process.exit(1);
  }
}

// Execute the main function
getTreasuryProposals().catch(error => {
  console.error(JSON.stringify({ error: error.message }));
  process.exit(1);
});