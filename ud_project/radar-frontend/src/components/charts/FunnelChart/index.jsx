import React from 'react';
import { ResponsiveFunnel } from '@nivo/funnel';
// import './funnelChart.scss'
export default function FunnelChart() {
    // const [hoverIndex, setHoverIndex] = useState(null);
    const data = [
        { id: 'Facebook', value: 1380 },
        { id: 'TikTok', value: 1100 },
        { id: 'Instagram', value: 990 },
        { id: 'X', value: 880 },
    ];

    const colors = ['#8571F4', '#287788', '#45D0EE', '#C686F8'];


    return (
    <>
    
        <div style={{ height: 200 }}>
            <ResponsiveFunnel
                data={data}
                margin={{ top: 20, right: 70, bottom: 20, left: 70 }}
                colors={colors}
                borderWidth={0}
                spacing={5}
                enableBeforeSeparators={false}
                enableAfterSeparators={false}
                isInteractive={true}
                currentPartSizeExtension={20} 
                    tooltip={'null'}
                    motionConfig="stiff"
            />
        </div>
        <div className="funnel-custom-legend">
                {data.map((item, index) => (
                    <div
                        key={index}
                        className="legend-item"
                        // onMouseEnter={() => setHoverIndex(index)}
                        // onMouseLeave={() => setHoverIndex(null)} 
                    >
                        <div
                            className="color-indicator"
                            style={{
                                backgroundColor: colors[index],
                            }}
                        />
                        <span className="label">{item.id}</span> 
                    </div>
                ))}
            </div>
            </>
    );
}