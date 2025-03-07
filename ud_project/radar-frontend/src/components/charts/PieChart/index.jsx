import React, { useEffect, useState } from 'react';
import ReactApexChart from 'react-apexcharts';


const facebookIcon = (
  <svg width="25" height="25" viewBox="0 0 25 25" fill="none" xmlns="http://www.w3.org/2000/svg">
    <g clip-path="url(#clip0_74_4569)" filter="url(#filter0_i_74_4569)">
      <path d="M18.3172 14.0625L19.0117 9.53826H14.6703V6.60233C14.6703 5.36483 15.2766 4.15779 17.2211 4.15779H19.1945V0.306232C19.1945 0.306232 17.4039 0.000762939 15.6914 0.000762939C12.1164 0.000762939 9.7797 2.16795 9.7797 6.09061V9.53904H5.80548V14.0633H9.7797V25.0008H14.6703V14.0633L18.3172 14.0625Z" fill="#5B7DF5"/>
    </g>
    <defs>
      <filter id="filter0_i_74_4569" x="0" y="0" width="25" height="29" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
        <feFlood flood-opacity="0" result="BackgroundImageFix"/>
        <feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape"/>
        <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha"/>
        <feOffset dy="4"/>
        <feGaussianBlur stdDeviation="7.5"/>
        <feComposite in2="hardAlpha" operator="arithmetic" k2="-1" k3="1"/>
        <feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.2 0"/>
        <feBlend mode="normal" in2="shape" result="effect1_innerShadow_74_4569"/>
      </filter>
      <clipPath id="clip0_74_4569">
        <rect width="25" height="25" fill="white"/>
      </clipPath>
    </defs>
  </svg>
);

const instagramIcon = (
  <svg width="25" height="25" viewBox="0 0 25 25" fill="none" xmlns="http://www.w3.org/2000/svg">
    <g filter="url(#filter0_i_74_4572)">
      <path fill-rule="evenodd" clip-rule="evenodd" d="M7.77603 1.06769C8.99791 1.01361 9.38749 1.00159 12.5 1.00159C15.6125 1.00159 16.0021 1.01461 17.2229 1.06769C18.4437 1.12078 19.2771 1.30808 20.0062 1.57951C20.7698 1.85696 21.4625 2.29065 22.0354 2.85155C22.6187 3.40143 23.0687 4.06649 23.3562 4.80167C23.6396 5.50279 23.8333 6.30407 23.8896 7.47595C23.9458 8.65283 23.9583 9.02743 23.9583 12.0192C23.9583 15.012 23.9448 15.3866 23.8896 16.5615C23.8344 17.7334 23.6396 18.5346 23.3562 19.2358C23.0687 19.971 22.618 20.6372 22.0354 21.1879C21.4625 21.7488 20.7698 22.1815 20.0062 22.4579C19.2771 22.7304 18.4437 22.9167 17.225 22.9707C16.0021 23.0248 15.6125 23.0368 12.5 23.0368C9.38749 23.0368 8.99791 23.0238 7.77603 22.9707C6.55728 22.9177 5.72395 22.7304 4.99478 22.4579C4.23012 22.1814 3.5373 21.748 2.96457 21.1879C2.38164 20.6377 1.93053 19.9718 1.6427 19.2368C1.36041 18.5356 1.16666 17.7344 1.11041 16.5625C1.05416 15.3856 1.04166 15.011 1.04166 12.0192C1.04166 9.02643 1.0552 8.65183 1.11041 7.47795C1.16561 6.30407 1.36041 5.50279 1.6427 4.80167C1.93095 4.06657 2.38241 3.40074 2.96561 2.85055C3.53753 2.29015 4.22965 1.8564 4.99374 1.57951C5.72291 1.30808 6.55624 1.12178 7.77499 1.06769H7.77603ZM17.1302 3.05087C15.9219 2.99778 15.5594 2.98676 12.5 2.98676C9.44061 2.98676 9.07811 2.99778 7.86978 3.05087C6.75207 3.09994 6.14582 3.27923 5.74166 3.43047C5.20728 3.63079 4.82499 3.86817 4.42395 4.25379C4.04379 4.60941 3.75122 5.04233 3.5677 5.52082C3.41041 5.90944 3.22395 6.49237 3.17291 7.56709C3.1177 8.72895 3.10624 9.07751 3.10624 12.0192C3.10624 14.9609 3.1177 15.3095 3.17291 16.4713C3.22395 17.5461 3.41041 18.129 3.5677 18.5176C3.75103 18.9954 4.04374 19.4291 4.42395 19.7846C4.79374 20.1502 5.24478 20.4317 5.74166 20.608C6.14582 20.7592 6.75207 20.9385 7.86978 20.9876C9.07811 21.0407 9.43957 21.0517 12.5 21.0517C15.5604 21.0517 15.9219 21.0407 17.1302 20.9876C18.2479 20.9385 18.8542 20.7592 19.2583 20.608C19.7927 20.4076 20.175 20.1703 20.576 19.7846C20.9562 19.4291 21.2489 18.9954 21.4323 18.5176C21.5896 18.129 21.776 17.5461 21.8271 16.4713C21.8823 15.3095 21.8937 14.9609 21.8937 12.0192C21.8937 9.07751 21.8823 8.72895 21.8271 7.56709C21.776 6.49237 21.5896 5.90944 21.4323 5.52082C21.249 5.04279 20.9562 4.60997 20.576 4.25432C20.2062 3.88868 19.7552 3.60719 19.2583 3.43047C18.8542 3.27923 18.2479 3.09994 17.1302 3.05087H17.1302ZM12.5 17.0592C15.1687 17.0592 17.3177 14.9102 17.3177 12.2425C17.3177 9.57483 15.1687 7.42595 12.5 7.42595C9.83124 7.42595 7.68228 9.57483 7.68228 12.2425C7.68228 14.9102 9.83124 17.0592 12.5 17.0592ZM12.5 15.0445C14.3058 15.0445 15.7984 13.5518 15.7984 11.746C15.7984 9.94023 14.3058 8.44756 12.5 8.44756C10.6942 8.44756 9.20162 9.94023 9.20162 11.746C9.20162 13.5518 10.6942 15.0445 12.5 15.0445ZM18.0714 7.37965C18.9003 7.37965 19.5714 6.70849 19.5714 5.87965C19.5714 5.0508 18.9003 4.37965 18.0714 4.37965C17.2426 4.37965 16.5714 5.0508 16.5714 5.87965C16.5714 6.70849 17.2426 7.37965 18.0714 7.37965Z" fill="#5B7DF5"/>
    </g>
    <defs>
      <filter id="filter0_i_74_4572" x="0" y="0" width="25" height="28" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
        <feFlood flood-opacity="0" result="BackgroundImageFix"/>
        <feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape"/>
        <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha"/>
        <feOffset dy="4"/>
        <feGaussianBlur stdDeviation="7.5"/>
        <feComposite in2="hardAlpha" operator="arithmetic" k2="-1" k3="1"/>
        <feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.2 0"/>
        <feBlend mode="normal" in2="shape" result="effect1_innerShadow_74_4572"/>
      </filter>
    </defs>
  </svg>
);


const tiktokIcon = (
  <svg width="20" height="23" viewBox="0 0 20 23" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M10.5053 0.0194073C11.7607 0 13.0088 0.0115006 14.2556 0C14.3311 1.46705 14.8591 2.96141 15.9339 3.99862C17.0066 5.06171 18.5238 5.54833 20 5.71293V9.5721C18.6166 9.52682 17.2267 9.23931 15.9713 8.64415C15.4246 8.39688 14.9153 8.07846 14.4167 7.75285C14.4102 10.5533 14.4282 13.3501 14.3987 16.139C14.3239 17.4788 13.8815 18.8121 13.1016 19.9162C11.847 21.7541 9.66936 22.9523 7.43274 22.9897C6.06083 23.0681 4.69037 22.6943 3.52134 22.0057C1.58398 20.8643 0.220714 18.7748 0.0221584 16.5321C-0.00285184 16.0572 -0.00669248 15.5814 0.0106479 15.1061C0.183305 13.2825 1.08616 11.538 2.48756 10.3513C4.076 8.96904 6.30111 8.31063 8.38451 8.70021C8.40393 10.1198 8.3471 11.538 8.3471 12.9576C7.39533 12.65 6.28313 12.7362 5.4515 13.3134C4.84306 13.7139 4.38326 14.3031 4.1429 14.9903C3.94435 15.4762 4.00118 16.016 4.01269 16.5321C4.24074 18.1048 5.75437 19.4267 7.37015 19.2837C8.44134 19.2722 9.46793 18.6511 10.0262 17.7419C10.2068 17.4234 10.4089 17.0978 10.4197 16.7233C10.5139 15.009 10.4765 13.3019 10.488 11.5876C10.496 7.7241 10.4765 3.87139 10.506 0.0201261L10.5053 0.0194073Z" fill="#5B7DF5"/>
</svg>
);
export default function PieChart({ data }) {
  const [hoverIndex, setHoverIndex] = useState(null);
  const [showIcons, setShowIcons] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      setShowIcons(window.innerWidth <= 1450);
    };

    window.addEventListener('resize', handleResize);

    handleResize(); // Call initially to set the state based on the current window size

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  // Check if data is defined and properly formatted
  const series = data && data.series ? JSON.parse((data.series).replace(/'/g, '"')) : [];
  const labels = data && data.labels ? JSON.parse((data.labels).replace(/'/g, '"')) : [];

  // Define gradients for each segment
  const gradients = [
    {
      from: '#4A7683',
      to: '#103542',
    },
    {
      from: '#7B96F9',
      to: '#3A62E8',
    },
    {
      from: '#60BAD0',
      to: '#287988',
    },
    {
      from: '#C452C4',
      to: '#710071',
    },
  ];

  // Generate colors array from gradients
  const colors = gradients.map(gradient => gradient.from);

  // Setup chart data and options
  const chartData = {
    series,
    options: {
      chart: {
        type: 'donut',
        height: 'auto',
        // offsetY: 10,
      
      },
      plotOptions: {
        pie: {
          donut: {
            size: '50%',
            background: 'transparent',
            labels: {
              show: true,
              name: {
                show: false,
                fontSize: '22px',
                fontFamily: 'Montserrat-Medium',
                fontWeight: 600,
                color: undefined,
                offsetY: -10
              },
              value: {
                show: false,
                fontSize: '16px',
                fontFamily: 'Montserrat-Medium',
                fontWeight: 400,
                color: undefined,
                offsetY: 16,
                formatter: function (val) {
                  return val
                }
              },
              total: {
                show: false,
                showAlways: false,
                label: 'Total',
                fontSize: '22px',
                fontFamily: 'Montserrat-Medium',
                fontWeight: 600,
                color: '#373d3f',
                formatter: function (w) {
                  return w.globals.seriesTotals.reduce((a, b) => {
                    return a + b
                  }, 0)
                }
              }
            }
          },
        },
      },
      stroke: {
        show: false,
      },
      dataLabels: {
        enabled: false,
      },
      labels,
      fill: {
        type: 'gradient',
        gradient: {
          shade: 'dark',
          type: 'horizontal',
          shadeIntensity: 0.8,
          gradientToColors: gradients.map(gradient => gradient.to),
          inverseColors: false,
          opacityFrom: .8,
          opacityTo: .8,
          stops: [0, 100],
        },
      },
      // colors: colors.map((color, index) => {
      //   const r = parseInt(color.slice(1, 3), 16);
      //   const g = parseInt(color.slice(3, 5), 16);
      //   const b = parseInt(color.slice(5, 7), 16);

      //   return hoverIndex === index
      //     ? `rgba(${r + 50}, ${g + 50}, ${b + 50}, 1)` // Make color brighter on hover
      //     : `rgba(${r}, ${g}, ${b}, 0.6)`; // Default color
      // }),
      colors: colors.map((color, index) =>
        hoverIndex === index
          ? `rgba(${parseInt(color.slice(1, 3), 16)}, ${parseInt(color.slice(3, 5), 16)}, ${parseInt(color.slice(5, 7), 16)}, 1)`
          : `rgba(${parseInt(color.slice(1, 3), 16)}, ${parseInt(color.slice(3, 5), 16)}, ${parseInt(color.slice(5, 7), 16)}, 0.6)`
      ),
      legend: {
        show: false,
      },
      tooltip: {
        enabled: true,
      },
    },
  };

  // Handle legend hover events
  const handleLegendHover = (index) => {
    setHoverIndex(index);
  };

  // Handle legend leave events
  const handleLegendLeave = () => {
    setHoverIndex(null);
  };


  const getIconForLabel = (label) => {
    switch (label.toLowerCase()) {
      case 'facebook':
        return facebookIcon;
      case 'instagram':
        return instagramIcon;
      case 'tiktok':
        return tiktokIcon;
      default:
        return label;
    }
  };

  return (
    <div className="row pie-container">
      <div className="pie-chart-wrapper" style={{ width: '30%', padding: 0 }}>
        <ReactApexChart
          options={chartData.options}
          series={chartData.series}
          type="donut"
          height={'100%'}
        />
      </div>

      <div className="custom-legend">
        {chartData.options.labels.map((label, index) => (
          <div
            key={index}
            className="legend-item"
            onMouseOver={() => handleLegendHover(index)}
            onMouseOut={handleLegendLeave}
          >
            <div
              className="color-indicator"
              style={{
                background: `linear-gradient(90deg, ${gradients[index].from}, ${gradients[index].to})`,
                opacity: hoverIndex === index ? 1 : 0.6,
              }}
            />
            <span className="label">
              {showIcons ? getIconForLabel(label) : label}
            </span>
            <span className="percentage">{chartData.series[index].toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
