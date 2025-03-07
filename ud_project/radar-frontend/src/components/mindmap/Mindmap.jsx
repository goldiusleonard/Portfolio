import G6 from "@antv/g6";
import React, { useEffect, useRef } from "react";
import "./mindmap.scss";
import endpoints from "../../config/config.dev";
import useApiData from "../../hooks/useApiData";
import LoaderAnimation from "../LoaderAnimation";
import { capitalizeFirstLetter, getUserFromLocalStorage } from "../../Util";

// const activeColor='#00FFFF'

const activeColor = "";
const user = getUserFromLocalStorage();

export const Mindmap = React.memo((props) => {
  const container = useRef(null);
  const apiEndpoint = endpoints.getMindMap;

  const { data: apiData, loading: apiLoading } = useApiData(`${apiEndpoint}?category=${props.currentCategory || ''}`);

  // Decide on the data source based on the role
  // const data = !props.currentCategory
  //   ? apiData
  //   : mindMapData.mindMapData.find(
  //     (category) =>
  //       category.label.toLowerCase() === props.currentCategory.toLowerCase()
  //   );

  // const loadingData = !props.currentCategory ? apiLoading : false;

  const refinedData = React.useMemo(() => {
    if (apiData && !apiLoading && Array.isArray(apiData.children)) {
      const newData = { ...apiData };
      newData.children.forEach((child) => {
        child.label = capitalizeFirstLetter(child.label);
        if (
          child.label?.toLocaleLowerCase() !== props.label?.toLocaleLowerCase()
        ) {
          child.collapsed = true;
        }
      });
      return newData;
    }
    return apiData;
  }, [apiData, apiLoading, props.label]);

  useEffect(() => {
    if (!refinedData) {
      return;
    }
    G6.registerNode("rectangleNode", {
      draw(cfg, group) {
        const hasExtra = !!(cfg?.aiFlaggedCount || cfg.newsCount);
        const aiFlaggedCountLength = cfg?.aiFlaggedCount?.length || 0;
        const labelLength = Math.max(
          cfg.label?.length,
          aiFlaggedCountLength + 12
        );

        const characterWidth = 5.5; // Approximate width of a character. Adjust as needed.
        const padding = 10; // Padding on each side of the text. Adjust as needed.

        const extraHeight = hasExtra
          ? aiFlaggedCountLength * 1.5 +
          15 -
          (!aiFlaggedCountLength && cfg.newsCount ? 50 : 0)
          : 0;

        let size = cfg.size || [
          labelLength * characterWidth + 2 * padding,
          40 + extraHeight,
        ];

        const width = size[0];
        const height = size[1];
        const yPosition =
          -height /
          (!cfg.newsCount && aiFlaggedCountLength ? 2.3 : extraHeight ? 4 : 2);
        const shape = group.addShape("rect", {
          attrs: {
            x: -width / 2,
            y: yPosition,
            width,
            height,
            fill: "#0B0B0B8C",
            stroke:
              cfg.label?.toLocaleLowerCase() ===
                props.label?.toLocaleLowerCase()
                ? activeColor
                : "",
            radius: 6,
            hoverCursor: "pointer",
            textTransform: "capitalize",
            // borderWith: 4,
          },
        });
        if (cfg.label) {
          group.addShape("text", {
            attrs: {
              text: cfg.label,
              fill: cfg.labelCfg.style.fill, // color of the text
              stroke: cfg.labelCfg.style.stroke, // outline color of the text
              radius: cfg.labelCfg.style.radius,
              color: cfg.labelCfg.style.color,
              lineWidth: cfg.labelCfg.style.lineWidth,
              fontSize: cfg.labelCfg.style.fontSize,
              fontFamily: cfg.labelCfg.style.fontFamily,
              padding: cfg.labelCfg.style.padding,
              fontWeight: 400,
              x: 0,
              y: 0,
              textAlign: "center",
              textBaseline: "middle",
              textTransform: "capitalize",
            },
          });
        }
        if (cfg.aiFlaggedCount) {
          group.addShape("text", {
            attrs: {
              text: "AI flagged: " + cfg.aiFlaggedCount,
              fill: "#A9A9A9", // color of the subtext
              // stroke:'red', // outline color of the subtext
              fontSize: cfg.labelCfg.style.fontSize * 0.75,
              // fontFamily: cfg.labelCfg.style.fontFamily,
              // Adjust the y position to place the subtext below the main text
              // You might need to adjust the value depending on the fontSize
              x: 0,
              y: 10, // Example offset, adjust as needed
              textAlign: "center",
              textBaseline: "top", // Align the top of the text to the y position
            },
          });

          if (cfg.newsCount) {
            group.addShape("text", {
              attrs: {
                text: "Total news: " + cfg.newsCount,
                fill: "#A9A9A9", // color of the subtext
                // stroke:'red', // outline color of the subtext
                fontSize: cfg.labelCfg.style.fontSize * 0.75,
                fontFamily: cfg.labelCfg.style.fontFamily,
                // Adjust the y position to place the subtext below the main text
                // You might need to adjust the value depending on the fontSize
                x: 0,
                y: 24, // Example offset, adjust as needed
                textAlign: "center",
                textBaseline: "top", // Align the top of the text to the y position
              },
            });
          }
        }

        return shape;
      },
      getAnchorPoints() {
        return [
          [0, 0.5], // left middle point
          [1, 0.5], // right middle point
        ];
      },
    });

    const graph = new G6.TreeGraph({
      container: container?.current,
      width: container?.current?.clientWidth - 20,
      height: container?.current?.clientHeight - 20,

      modes: {
        default: [
          {
            type: "collapse-expand",
            onChange: function onChange(item, collapsed) {
              const data = item.get("model");
              data.collapsed = collapsed;

              graph.refreshLayout();
              graph.render(false);
              graph.fitView();

              return true;
            },
            enableOptimize: true,
          },

          // {
          //   type: 'drag-node',
          //   enableDelegate: true,
          // },
        ],
      },

      defaultNode: {
        type: "rectangleNode",

        labelCfg: {
          style: {
            fill: "#FFFFFF",
            textTransform: "capitalize",
          },
        },
        linkPoints: {
          top: false,
          bottom: false,
          left: true,
          right: true,
          size: 5,
        },
      },
      defaultEdge: {
        type: "cubic-horizontal",
        style: {
          stroke: "#A3B9CC",
          // fill: '#353535',
        },
      },
      layout: {
        type: "mindmap",
        direction: "LR",
        getId: function getId(d) {
          return d.id;
        },
        getHeight: function getHeight() {
          return container.current.clientHeight / 30;
        },
        getHGap: function getHGap(e) {
          return container.current.clientWidth / 10;
        },
        getZoom: function getZoom() {
          return 1;
        },
      },
    });

    graph.on("node:click", (evt) => {
      const { item } = evt;
      const model = item.getModel();
      const parentNode = evt?.item;
      const subcategory = parentNode?._cfg?.parent?._cfg?.parent?._cfg?.model;
      if (!!subcategory) {
        props.setCategory(subcategory.key, subcategory.label);
      }
      const { key, label } = model;

      props.setCategory(key, label);
    });

    graph.data(refinedData);
    graph.layout();
    graph.render(true);
    graph.fitView();

    return () => {
      graph.destroyLayout();
    };
  }, [props.label, refinedData, apiLoading, props]);

  return apiLoading ? (
    <LoaderAnimation />
  ) : (
    <div ref={container} className="mind-map" />
  );
});
