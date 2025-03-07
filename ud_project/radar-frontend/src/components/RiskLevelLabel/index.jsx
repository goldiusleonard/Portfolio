import React from 'react'
import { Button } from 'reactstrap';

const CustomBox = (data) => {
    const colors = {
        low: {
            color: '#FFE700',
            borderColor: '#FFE700',
            backgroundColor: 'rgba(255, 231, 0, 0.20)',
        },
        medium: {
            color: '#FF8C00',
            borderColor: '#FF8C00',
            backgroundColor: 'rgba(255, 140, 0, 0.20)',
        },
        high: {
            color: '#F12D2D',
            borderColor: '#F12D2D',
            backgroundColor: 'rgba(241, 45, 45, 0.20)',
        },
    };

    return colors[data] || {};
};

const RiskLevelLabel = ({ riskLevel }) => {
    return (
        <>
            <Button className='content-details-card-btn text-capitalize'
                style={{ ...CustomBox(riskLevel) }}
                size='sm'
            >
                {riskLevel}
            </Button>
        </>
    )
}

export default RiskLevelLabel
