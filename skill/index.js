/**
 * Nous Miner Skill
 * 
 * Your AI mines. You earn.
 */

module.exports = {
  name: 'nous-miner',
  version: '1.0.0',
  description: 'Mine Nous cryptocurrency with your AI agent',
  
  commands: {
    status: 'Show mining status',
    start: 'Start mining',
    stop: 'Stop mining',
    balance: 'Check balances',
    wallet: 'Show wallet addresses',
    setup: 'Initial setup'
  },
  
  network: {
    seedNode: '23.22.111.244:9000',
    rpcEndpoint: 'http://23.22.111.244:9001/rpc',
    blockTime: 600,
    blockReward: 50
  }
};
