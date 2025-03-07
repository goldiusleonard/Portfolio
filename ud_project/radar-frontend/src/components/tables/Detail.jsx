import React from 'react';
import { useNavigate } from 'react-router-dom';
import { detail_img } from '../../assets/images';
import DownArrowIcon from '../../assets/icons/DownArrowIcon';



export default function Detail(props) {
    const navigate = useNavigate();
    const goToContentDetail = () => {
        navigate('/category-details/content-details');
    }

    return (
        <div className='table-detail'>
            <div className='close-popup'>
                <span onClick={() => props.setSelectId(null)} style={{cursor: 'pointer'}}>
                <DownArrowIcon fill="#fff" size="15" deg="90deg" />
                </span>
                <h4>{props.id}</h4>
            </div>
            <img src={detail_img} alt='placeholder' width='120' height='218' />
            <div className="justification-container">
                <div className='title' >Justification</div>
                <div className='detail-text'>
                    <p >
                        According to the video, there are strong indications that the content might be
                        high likely a scam. This is suggested by the involvement of a person associated with OctaFX,
                        a company already listed by Bank Negara Malaysia and Securities Commission Malaysia as an unauthorised entity.
                        Additionally, the video promises high returns on investment for joining their group, a claim that appears suspiciously unrealistic.
                    </p>
                </div>
            </div>

            <div className='button-container'>
                <button className='table-button table-button-selectAll' onClick={props.handleOpenModal}>Report Content</button>
                <button className='table-button table-button-report' onClick={goToContentDetail}>Content Details</button>
            </div>



        </div>
    )
}