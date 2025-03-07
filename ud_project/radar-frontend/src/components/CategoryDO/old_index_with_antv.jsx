import React, { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom';
import G6 from '@antv/g6'
// import data from './data'
import useApiData from '../../hooks/useApiData'
import endpoints from '../../config/config.dev';
import LoaderAnimation from '../LoaderAnimation';

const CategoryDO = () => {
  const containerRef = useRef(null)
  const location = useLocation()
  const { video_id: contentID } = location.state ? location.state : [];
  const apiEndpoint = `${endpoints.getCategoryDO}?video_id=${contentID}` 
  const { data, loadingData } = useApiData(apiEndpoint)


  useEffect(() => {
    if (!containerRef.current) return

    G6.registerNode('custom-node', {
      draw(cfg, group) {
        const width = 110;
        const height = 45;
        const borderRadius = 6;
        const fontSize = 14;
        const maxLineLength = 10; 

        // Draw the rectangle
        const rect = group.addShape('rect', {
          attrs: {
            x: -width / 2,
            y: -height / 2,
            width,
            height,
            stroke: '#353535',
            fill: '#14181D',
            radius: borderRadius,
            lineWidth: 2,
          },
          name: 'rect-shape',
        });

        // Function to split text into lines
        const splitTextIntoLines = (text, maxLineLength) => {
          const lines = [];
          let currentLine = '';
          for (let i = 0; i < text.length; i++) {
            currentLine += text[i];
            if (currentLine.length >= maxLineLength) {
              lines.push(currentLine);
              currentLine = '';
            }
          }
          if (currentLine.length > 0) {
            lines.push(currentLine);
          }
          return lines;
        };

        const lines = splitTextIntoLines(cfg.label, maxLineLength);
        const totalTextHeight = lines.length * fontSize;
        const startY = -totalTextHeight / 2 + fontSize / 2;

        lines.forEach((line, index) => {
          group.addShape('text', {
            attrs: {
              text: line,
              x: 0,
              y: startY + index * fontSize,
              textAlign: 'center',
              textBaseline: 'middle',
              fill: '#00FFFF',
              fontSize,
            },
            name: 'text-shape',
          });
        });

        return rect;
      },
    });

    // if (data) {
    if (!loadingData && data) {
      const graph = new G6.Graph({
        container: containerRef.current,
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight,
        fitView: true,
        fitViewPadding: 10,
        animate: true,
        layout: {
          type: 'fruchterman',
          gravity: 3,
          speed: 7,
          tick: () => {
            graph.refreshPositions()
          },
        },
        defaultNode: {
          type: 'custom-node',
          size: [100, 40],
          color: '#353535',
          // style: {
          //   lineWidth: 2,
          //   fill: '#14181D',
          //   radius: 6,
          //   color: '#00FFFF'
          // },
          // labelCfg: {
          //   position: 'center',
          //   style: {
          //     color: '#00FFFF',
          //     fill: '#00FFFF',
          //   },
          // }
        },
        defaultEdge: {
          size: 1,
          color: '#353535'
        },
        modes: {
          default: ['drag-canvas', 'drag-node'],
        },
      });

      // const nodes = data.nodes;
      const nodes = data.nodes.map(node => ({
        ...node,
        type: 'custom-node',
      }));
      graph.data({
        nodes,
        edges: []
      });
      graph.render();
      return () => {
        graph.destroy();
      };
    }
  }, [data, loadingData])

  return (
    <div className='do-container p-3'>
      {loadingData ? (
        <LoaderAnimation />
      ) : (
        data ? (
          <div ref={containerRef} style={{ height: '100%', width: '100%' }}></div>
        ) : (
          <div>No data available</div>
        )
      )}
    </div>
  )
}

export default CategoryDO
