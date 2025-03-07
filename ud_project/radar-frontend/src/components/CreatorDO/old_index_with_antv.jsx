import React, { useEffect, useRef } from 'react'
import G6 from '@antv/g6'
import data from './categoryDO.json'
import useApiData from '../../hooks/useApiData';
import endpoints from '../../config/config.dev';
import { useGlobalData } from '../../App';
import LoaderAnimation from '../LoaderAnimation';
import { useLocation } from 'react-router-dom';

G6.registerNode('custom-node', {
  jsx: (cfg) => `
    <group>
      <rect style={{
        width: 80,
        height: 120,
      }}>
        <rect style={{
          width: 80,
          height: 120,
          fill: '#0d1116',
          radius: [5, 5, 5, 5],
          cursor: 'move'，
          stroke: 'blue',
          strokeSize: 5,
        }} draggable="true">
          
          <circle style={{
            stroke: ${cfg.color},
            r: 25,
            fill: '#fff',
            marginLeft: 40,
            marginTop: 40,
            cursor: 'pointer'
          }} name="circle">
            <image name="img" style={{ img: ${cfg.picture}, width: 50, height: 50,  marginLeft: 15,  marginTop: -18 }} />
          </circle>

          <text style={{
            marginTop: 20,
            marginLeft: 40,
            textAlign: 'center',
            fontWeight: 'bold',
            fill: '#00FFFF' }}>{{label}}</text>

          <text style={{
            marginTop: 20,
            marginLeft: 40,
            textAlign: 'center',
            fontWeight: 'bold',
            fill: '#F12D2D' }}>${cfg.percentage}%</text>
        </rect>
      </rect>
    </group>
  `,
});

const CreatorDO = ({creatorName}) => {
  const containerRef = useRef(null)
  // // const { creatorUsername } = useGlobalData()
  // const location = useLocation
  // const { user_handle: creatorUsername } = location.state ? location.state : [];
  const apiEndpoint = `${endpoints.getProfileDO}?userName=${creatorName}`
  const { data, loadingData } = useApiData(apiEndpoint)

  useEffect(() => {
    if (!containerRef.current) return

    if (!loadingData && data) {
    // if (data) {
      const graph = new G6.Graph({
        container: containerRef.current,
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight,
        fitView: true,
        fitViewPadding: 10,
        animate: true,
        layout: {
          type: 'fruchterman',
          gravity: 2,
          speed: 7,
          tick: () => {
            graph.refreshPositions()
          },
        },
        defaultNode: {
          // type: 'rect',
          // size: [80, 40],
          // color: '#353535',
          type: 'custom-node',
          style: {
            lineWidth: 2,
            fill: '#14181D',
            radius: 6,
            color: '#00FFFF',
            stroke: '#FFF'
          },
          labelCfg: {
            position: 'center',
            style: {
              color: '#00FFFF',
              fill: '#00FFFF',
            },
          }
        },
        defaultEdge: {
          size: 3,
          color: '#353535',
          // width: 80
          // type: 'cubic-horizontal',
        },
        modes: {
          default: ['drag-canvas', 'zoom-canvas', 'drag-node'],
        },
      });

      const nodes = data.nodes;
      graph.data({
        nodes,
        edges: []
        // edges: data.edges.map(function (edge, i) {
        //   edge.id = 'edge' + i;
        //   return Object.assign({}, edge);
        // })
      });
      graph.render();
      return () => {
        graph.destroy();
      };
    }
    }, [data, loadingData])
    // }, [data])

  return (
    <div className='p-3 do-container'>
      {loadingData ? <LoaderAnimation /> : (
        data ? (
          <div ref={containerRef} style={{ height: '100%', width: '100%' }}></div>
        ) : (
          <div>No data available</div>
        )
      )}
    </div>
  )
}

export default CreatorDO