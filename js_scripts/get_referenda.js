/**
 * Script to fetch active referenda from the Polkadot network
 * This script is executed by Python using subprocess
 */

import { createClient } from 'polkadot-api';
import { dot } from '@polkadot-api/descriptors';
import { getWsProvider } from 'polkadot-api/ws-provider/node';
import { withPolkadotSdkCompat } from 'polkadot-api/polkadot-sdk-compat';
import { createReferendaSdk } from '@polkadot-api/sdk-governance';

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

async function getReferenda() {
  // Create a client with the WebSocket provider
  const client = createClient(
    withPolkadotSdkCompat(getWsProvider(endpoint))
  );

  try {
    // Get the typed API for Polkadot
    const api = client.getTypedApi(dot);
    // Initialize the referenda SDK
    const referendaSdk = await createReferendaSdk(api);

    // Fetch all referenda
    const referenda = await referendaSdk.getReferenda();

    // Filter to get only ongoing referenda
    const ongoingReferenda = referenda.filter(r => r.type === 'Ongoing');

    // Build the result
    const result = [];
    for (const ref of ongoingReferenda) {
      // Fetch the proposal's calldata
      const proposal = await ref.proposal.resolve();
      // Fetch the decoded call (section, method, arguments)
      const decodedCall = await ref.proposal.decodedCall();
      // Fetch track details
      const track = await ref.getTrack();

      // Calculate the start and end of the confirmation period
      const confirmationStart = await ref.getConfirmationStart();
      const confirmationEnd = await ref.getConfirmationEnd();

      // Add to the result
      result.push({
        index: ref.index,
        track: {
          id: ref.trackId,
          name: track.name,
          info: {
            preparePeriod: track.preparePeriod,
            decisionPeriod: track.decisionPeriod,
            confirmPeriod: track.confirmPeriod,
            minApproval: track.minApproval ? track.minApproval.toString() : null,
            minSupport: track.minSupport ? track.minSupport.toString() : null
          }
        },
        proposal: {
          rawValue: typeof ref.proposal.rawValue === 'bigint' ? ref.proposal.rawValue.toString() : ref.proposal.rawValue,
          callData: proposal.toString('hex'),
          decodedCall: {
            section: decodedCall.type,
            method: decodedCall.value ? decodedCall.value.type : null,
            args: decodedCall.value ? convertBigIntsToString(decodedCall.value.value) : null
          }
        },
        status: {
          tally: {
            ayes: ref.tally.ayes.toString(),
            nays: ref.tally.nays.toString(),
            support: ref.tally.support.toString()
          },
          submittedAt: ref.submittedAt,
          decidingAt: ref.decidingAt,
          decisionDeposit: ref.decisionDeposit ? {
            who: ref.decisionDeposit.who,
            amount: ref.decisionDeposit.amount.toString()
          } : null,
          confirmationPeriod: {
            start: confirmationStart,
            end: confirmationEnd
          }
        }
      });
    }

    // Print as JSON for Python to capture
    console.log(JSON.stringify(result));

    // Disconnect the client
    client.destroy();
  } catch (error) {
    // Print error as JSON for Python to capture
    console.error(JSON.stringify({ error: error.message }));
    process.exit(1);
  }
}

// Execute the main function
getReferenda().catch(error => {
  console.error(JSON.stringify({ error: error.message }));
  process.exit(1);
});