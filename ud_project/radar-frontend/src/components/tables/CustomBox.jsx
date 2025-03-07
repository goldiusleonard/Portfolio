

export const CustomBox = (rowData) => {

    const color = rowData.risk_status === 'low' ? '#FFE700' : rowData.risk_status === 'medium' ? '#FF8C00' : '#F12D2D';
    const borderColor = rowData.risk_status === 'low' ? '#FFE700' : rowData.risk_status === 'medium' ? '#FF8C00' : '#F12D2D';
    const backgroundColor = rowData.risk_status === 'low' ? "rgba(255, 231, 0, 0.20) " : rowData.risk_status === 'medium' ? "rgba(255, 140, 0, 0.20) " : 'rgba(241, 45, 45, 0.20)';


    return (

        <button className='table-button' style={{ color, borderColor, backgroundColor, width: 122, textTransform: 'capitalize' }}>{rowData.risk_status}</button>


    );
};

export const CustomRiskBox = (rowData) => {

    const color = rowData.risk_level === 'low' ? '#FFE700' : rowData.risk_level === 'medium' ? '#FF8C00' : '#F12D2D';
    const borderColor = rowData.risk_level === 'low' ? '#FFE700' : rowData.risk_level === 'medium' ? '#FF8C00' : '#F12D2D';
    const backgroundColor = rowData.risk_level === 'low' ? "rgba(255, 231, 0, 0.20) " : rowData.risk_level === 'medium' ? "rgba(255, 140, 0, 0.20) " : 'rgba(241, 45, 45, 0.20)';


    return (

        <button className='table-button' style={{ color, borderColor, backgroundColor, width: 122, textTransform: 'capitalize' }}>{rowData.risk_level}</button>


    );
};

export const WSCustomBox = (rowData) => {

    const color = rowData.risk_statustoLowerCase() === 'low' ? '#FFE700' : rowData.risk_statustoLowerCase() === 'medium' ? '#FF8C00' : '#F12D2D';
    const borderColor = rowData.risk_statustoLowerCase() === 'low' ? '#FFE700' : rowData.risk_statustoLowerCase() === 'medium' ? '#FF8C00' : '#F12D2D';
    const backgroundColor = rowData.risk_statustoLowerCase() === 'low' ? "rgba(255, 231, 0, 0.20) " : rowData.risk_statustoLowerCase() === 'medium' ? "rgba(255, 140, 0, 0.20) " : 'rgba(241, 45, 45, 0.20)';


    return (

        <button className='table-button' style={{ color, borderColor, backgroundColor, width: 122, textTransform: 'capitalize' }}>{rowData.risk}</button>


    );
};