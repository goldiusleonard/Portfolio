import React, { useEffect, useRef } from 'react';
import { Timeline } from 'primereact/timeline';
import facebook from '../../assets/images/facebook.png';
import './scrollableList.scss';
import { useNavigate } from 'react-router-dom';

export default function TemplateDemo({ highlightedContent, name, setDate, selectedYear, date, data }) {
    const navigate = useNavigate();
    const timelineRef = useRef(null);

    useEffect(() => {
        setDate(null)
        if (timelineRef.current && data.length > 0) {
            const firstItem = data[0];
            const element = document.getElementById(`timeline-item-${firstItem.date}`);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    }, [selectedYear]);

    useEffect(() => {
        setDate(null)
        if (timelineRef.current && date) {
            const element = document.getElementById(`timeline-item-${date}`);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    }, [date, data]);

    const handleClick = (video_id) => {
        navigate('/category-details/content-details', { state: { video_id } });
    }


    const customizedMarker = (item) => {

        return (
            <div className='position-relative' style={{ top: '45%', padding: '10px 0', background: '#0D1117' }}>
                <div className="p-timeline-event-connector d-none" data-pc-section="connector"></div>
                <span className="flex w-2rem h-2rem align-items-center justify-content-center text-white border-circle z-1 shadow-1" style={{ backgroundColor: '#14181D', width: 40, height: 40, borderRadius: "50%", borderColor: '#353535', borderWidth: 1, display: 'flex', justifyItems: 'center', justifyContent: 'center', visibility: item.content ? 'visible' : 'hidden', cursor: 'pointer' }}
                    onClick={(event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        window.open(`https://www.tiktok.com/@${name}/video/${item?.url?.match(/\/(\d+)\.mp4/)[1]}`, '_blank', 'noopener,noreferrer');
                    }}>
                    {item?.socialMedia === 'TikTok' ?
                        <svg
                            xmlns="http://www.w3.org/2000/svg" width="11" height="15" viewBox="0 0 34 39" fill="none">
                            <path d="M17.3525 0.848185C19.4261 0.816101 21.4878 0.835114 23.5471 0.816101C23.6719 3.24142 24.5441 5.7119 26.3194 7.42661C28.0912 9.18411 30.5973 9.98859 33.0357 10.2607V16.6407C30.7506 16.5658 28.4548 16.0905 26.3812 15.1066C25.4781 14.6978 24.6368 14.1714 23.8133 13.6331C23.8026 18.2627 23.8323 22.8864 23.7836 27.497C23.66 29.712 22.9292 31.9163 21.6411 33.7415C19.5687 36.78 15.9717 38.7609 12.2773 38.8227C10.0112 38.9522 7.74748 38.3343 5.81649 37.1959C2.6164 35.3089 0.364572 31.8545 0.0366008 28.147C-0.00471062 27.3618 -0.0110545 26.5752 0.017588 25.7894C0.30278 22.7747 1.7941 19.8907 4.1089 17.9288C6.73267 15.6437 10.4081 14.5552 13.8494 15.1993C13.8815 17.5462 13.7876 19.8907 13.7876 22.2376C12.2155 21.729 10.3784 21.8716 9.0047 22.8258C7.99969 23.4879 7.24019 24.462 6.84318 25.5981C6.51521 26.4014 6.60909 27.2938 6.6281 28.147C7.00479 30.747 9.50497 32.9323 12.1739 32.6958C13.9433 32.6768 15.639 31.6501 16.5611 30.1469C16.8594 29.6205 17.1933 29.0822 17.2111 28.4631C17.3668 25.629 17.305 22.8068 17.324 19.9727C17.3371 13.5856 17.305 7.21628 17.3537 0.849373L17.3525 0.848185Z" fill="#5B7DF5" />
                        </svg>
                        :
                        <svg width="11" height="15" viewBox="0 0 22 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M20.3075 22.5L21.4188 15.2612H14.4725V10.5637C14.4725 8.58372 15.4425 6.65247 18.5538 6.65247H21.7113V0.489971C21.7113 0.489971 18.8463 0.0012207 16.1063 0.0012207C10.3863 0.0012207 6.64751 3.46872 6.64751 9.74497V15.2625H0.288757V22.5012H6.64751V40.0012H14.4725V22.5012L20.3075 22.5Z" fill="#5B7DF5" />
                        </svg>
                    }
                </span>
            </div>
        );
    };


    let lastRenderedDate = null;
    const customizedContent = (item) => {
        const showDate = item.date !== lastRenderedDate;
        lastRenderedDate = item.date;

        if (!item.content) {
            return (
                <div id={`timeline-item-${item.date}`} style={{ display: 'flex', alignItems: 'center', }} className='list-content'>
                    {showDate && (
                        <div className='list-date' style={{ marginLeft: -70, width: '7rem' }}>
                            {item.date}
                        </div>
                    )}
                    <hr
                        style={{
                            width: '100%',
                            backgroundColor: '#353535',
                            marginLeft: 5
                        }}
                    />
                </div>
            );
        }

        return (
            <>
                <div id={`timeline-item-${item.date}`} style={{ display: 'flex', alignItems: 'center', marginBottom: '5rem' }} className='list-content'>
                    {showDate && (
                        <div className='list-date' style={{ marginLeft: '-35px', width: '11rem' }}>
                            {item.date}
                        </div>
                    )}
                    <hr
                        style={{
                            width: '100%',
                            backgroundColor: '#353535',
                            marginLeft: '-5px'
                        }}
                    />
                </div>
                <div id={`timeline-item-${item.date}`} className='list-content'>
                    <div className='list-title'>
                        {item.type}
                    </div>
                    <div className='list-content-text'>
                        <div style={{ cursor: 'pointer' }} onClick={() => handleClick(item?.video_id)}>
                            {item.content}
                        </div>
                        <div className='list-content-footer'>
                            <a href={item.url} target="_blank" rel="noopener noreferrer">
                                Download Video
                            </a>
                            <CustomBox riskRate={item.riskRate} />
                        </div>
                    </div>
                </div>
            </>
        );
    };


    const filteredData = highlightedContent.length > 0
        ? data.filter(item => highlightedContent.includes(item?.video_id))
        : data;


    // const transformedData = [];

    // data.forEach((item, index) => {
    //     if (item.date && filteredData.some(fItem => fItem.video_id === data[index + 1]?.video_id)) {
    //         transformedData.push({ date: item.date });
    //     }

    //     const filteredItem = filteredData.find(fItem => fItem.video_id === item.video_id);

    //     if (filteredItem) {
    //         transformedData.push(filteredItem);
    //     }
    // });

    return (
        <div ref={timelineRef} className="cont-wrapper">
            {
                data.length > 0 && highlightedContent.length > 0 ? (
                    <Timeline value={filteredData} align="left" marker={customizedMarker} content={customizedContent} />
                ) : data.length > 0 && highlightedContent.length === 0 ? (
                    <Timeline value={data} align="left" marker={customizedMarker} content={customizedContent} />
                ) : (
                    <div className='list-empty'>Threats not found</div>
                )
            }

        </div>
    )
}

const CustomBox = ({ riskRate }) => {
    const color = riskRate?.toLowerCase() === 'low' ? '#FFE700' : riskRate?.toLowerCase() === 'medium' ? '#FF8C00' : '#F12D2D';
    const borderColor = riskRate?.toLowerCase() === 'low' ? '#FFE700' : riskRate?.toLowerCase() === 'medium' ? '#FF8C00' : '#F12D2D';
    const backgroundColor = riskRate?.toLowerCase() === 'low' ? "rgba(255, 231, 0, 0.20)" : riskRate?.toLowerCase() === 'medium' ? "rgba(255, 140, 0, 0.20)" : 'rgba(241, 45, 45, 0.20)';

    return (
        <button className='table-button' style={{ color, borderColor, backgroundColor, width: 122, textTransform: 'capitalize' }}>
            {riskRate}
        </button>
    );
};
