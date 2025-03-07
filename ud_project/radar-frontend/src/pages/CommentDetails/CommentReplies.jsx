import React from 'react';
import sample_profile_image from '../../assets/images/avatar.png'
import CommentWithReply from './CommentWithReply';
const CommentReplies = () => {
    return (
        <TabLayout />
    );
};

export default CommentReplies;


const categories = [
    'Hate Speech',
    'scam',
    'racism',
    'Sexual Harassment',
    'Violence',
]


const TabLayout = ({ data }) => {
    const [activeTab, setActiveTab] = React.useState(0);

    const handleTabClick = (index) => {
        setActiveTab(index);
    };

    return (
        <div className="tab-layout card-wrap  ">
            <div className="tab-header">
                <div
                    className={`tab-item ${activeTab === 0 ? 'active' : ''}`}
                    onClick={() => handleTabClick(0)}
                >
                    Main Comment
                </div>
                <div
                    className={`tab-item ${activeTab === 1 ? 'active' : ''}`}
                    onClick={() => handleTabClick(1)}
                >
                    Replied By
                </div>
            </div>
            <div className="tab-content-container">
                {activeTab === 0 && (
                    <div className="main-comment">
                        <div className='body'>

                            <div style={{ cursor: 'pointer' }} >
                                <img src={!data?.creator_img || data?.creator_img.includes("https://p16-sign") ? sample_profile_image : data?.creator_img} alt='profile' />
                            </div>

                            <div className='sec'>
                                <span className='text-capitalize'>{data?.creator_name ?? 'Jane Doe'}</span>
                                <div className='pt-2 gap-2 d-flex'>
                                    {categories.slice(0, 3).map((item, index) => (
                                        <div className='bordered-container' key={index}>
                                            {item}
                                        </div>
                                    ))
                                    }
                                    {categories.length > 3 && (
                                        <div className="bordered-container hover-btn">
                                            <div className="trigger">
                                                +
                                                {categories.length - 3}
                                            </div>
                                            <div className="dropdown-content">
                                                {categories.slice(3).map((item, index) => (
                                                    <div className="tag" key={index}>
                                                        {item}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>

                            </div>

                            <div className='right-side-align '>
                                <p className='tertiary-title pb-2'>Engagement</p>
                                <p>85%</p>
                            </div>
                        </div>

                        <div className='comment-container'>
                            Lorem ipsum dolor sit amet consectetur. Magna scelerisque ultrices consectetur quis sit auctor diam. Auctor id aliquam amet fringilla donec ut convallisLorem ipsum dolor sit amet consectetur. Magna scelerisque ultrices consectetur quis sit auctor diam. Auctor id aliquam amet fringilla donec ut convallis cursus. Pretium vel sapien pharetra in. Lobortis detiam ac tellus. cursus. Pretium vel sapien pharetra in. Lobortis detiam ac tellus.
                        </div>


                    </div>
                )}
                {activeTab === 1 && (
                    <div >
            
                        <CommentWithReply />
                    
                    </div>
                )}
            </div>
        </div>
    );
};

