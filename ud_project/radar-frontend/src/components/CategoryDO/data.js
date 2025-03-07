const data = {
    nodes: [
      { id: 'node0', label: 'Bitcoin'  },
      { id: 'node1', label: 'Ethereum'},
      { id: 'node2', label: 'Tether' },
      { id: 'node3', label: 'USD Coin' },
      { id: 'node4', label: 'Cardano' },
      { id: 'node5', label: 'BNB' },
    ],
    edges: [
      { source: 'node0', target: 'node1' },
      { source: 'node0', target: 'node2' },
      { source: 'node0', target: 'node3' },
      { source: 'node0', target: 'node4' },
      { source: 'node0', target: 'node5' },
    ]
  };

  export default data;