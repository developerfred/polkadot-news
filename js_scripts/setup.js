
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
            