import React from 'react';
import sample_profile_image from '../../assets/images/avatar.png';
import './modal.scss'

const ModalComponent = () => {
    <div>
        <div className="mb-3">Creator Detail</div>
        <div className="creator-detail flex-column h-100 align-items-start">
            <div className='creator-detail-profile'>
                <img src={sample_profile_image} alt='profile' />
                <div className='creator-id-container'>
                    <p className='creator-id'>#1 Jane Cooper</p>
                </div>
            </div>
            <div className="d-flex justify-content-between w-100">
                <div className='creator-details-cards'>
                    <div className='creator-details-cards-title'>Following</div>
                    <div className='creator-details-cards-content'>9M</div>
                </div>
                <div className='creator-details-cards'>
                    <div className='creator-details-cards-title'>Followers</div>
                    <div className='creator-details-cards-content'>908</div>
                </div>
                <div className='creator-details-cards'>
                    <div className='creator-details-cards-title'>Posts</div>
                    <div className='creator-details-cards-content'>789</div>
                </div>
                <div className='creator-details-cards'>
                    <div className='creator-details-cards-title'>Engagement</div>
                    <div className='creator-details-cards-content'>95%</div>
                </div>
            </div>
        </div>

        <div>
            <div className="my-4">Send content report to External Organization (Optional)</div>
            <div className="creator-detail-input-wrapper">
                <div className="input-title">Report Subject</div>
                <select>
                    <option>Choose a subject for your email template</option>
                </select>
            </div>
            <div className="creator-detail-input-wrapper">
                <div className="input-title">Select Organization</div>
                <select>
                    <option>Choose list organization who will receive this email</option>
                </select>
            </div>
            <div className="creator-detail-input-wrapper">
                <div className="input-title">Send to custom email</div>
                <input type="email" placeholder="Type list of email who will receive this email  " />
            </div>
        </div>
    </div>

}

export default ModalComponent;