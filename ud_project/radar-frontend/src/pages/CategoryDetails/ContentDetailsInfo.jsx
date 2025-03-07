import Button from "../../components/button/Button"
import { FacebookIcon, ContentCopy, ArrowRight } from "../../assets/icons"
import GlobalInnerCard from "./GlobalInnerCard"

const ContentDetailsInfo = () => {
    return (
        <div className="content-details-wrapper">
            <div className="content-details-info">
                <div className="social-media-info">
                    <img src={FacebookIcon} alt="Facebook icon" />
                    <div>
                        <p className="content-id">FB240228CBMM000014 <img src={ContentCopy} alt="Content copy icon" /></p>
                        <span className="date-time">17:03</span><span className="date-time">Oct 11, 2024</span>
                    </div>
                </div>
                <Button className='outline' text={
                    <div className="d-flex align-items-center">
                        View Content Details
                        <img src={ArrowRight} alt="Arrow right icon" />
                    </div>
                } />
            </div>
            <div className="content-details-stats">
                <div className='content-details-cards'>
                    <div className='content-details-cards-title'>Status</div>
                    <div className='content-details-cards-content'>Reported</div>
                </div>
                <div className='content-details-cards'>
                    <div className='content-details-cards-title'>Likes</div>
                    <div className='content-details-cards-content'>24,000</div>
                </div>
                <div className='content-details-cards'>
                    <div className='content-details-cards-title'>Comments</div>
                    <div className='content-details-cards-content'>908</div>
                </div>
                <div className='content-details-cards'>
                    <div className='content-details-cards-title'>Shares</div>
                    <div className='content-details-cards-content'>11.42</div>
                </div>
                <div className='content-details-cards'>
                    <div className='content-details-cards-title'>Risk Level</div>
                    <div className='content-details-cards-content risk high'>High</div>
                </div>
            </div>
            <div className="d-flex gap-3 mt-4">
                <div className="original-content-body">
                    <div className="original-content-img">
                        {/* {data?.content_img ?
                            <img src={data?.content_img} alt="content" />
                            :
                            <div className="empty-image"></div>
                        } */}
                        <div className="btn-play-overlay">
                            <i className="pi pi-play-circle"></i>
                        </div>
                    </div>
                    <div className="download-btn-wrapper">
                        {/* <a href={data?.content_url} target="_blank" rel="noopener noreferrer">

                            <i className="pi pi-cloud-download" style={{ fontSize: '1.75rem', color: '#00FFFF', marginRight: 8 }}></i>
                        </a> */}

                    </div>
                </div>
                <div className="outer-card">
                    <p className="card-title">Posted By</p>
                    <GlobalInnerCard>
                        <div className="left">
                            <img src='https://s3-alpha-sig.figma.com/img/78d9/96ec/fa1be286e3b17627a17bbb20e41bbdc5?Expires=1735516800&Key-Pair-Id=APKAQ4GOSFWCVNEHN3O4&Signature=MALGNpki0oUdLWg5nkdne~ntnTsWOHL3RQp7YypAWM5NtvuMFnNVGGmjFTtQIjwwUqayB2SEGa79wTsocMREeO6ypDnYUPIVUYfUBdYXILd9k0Gqcj4mjn04vMubq0ckA5jy8rvWieuBMno-O0M3fr7dwPoFvoTdlUZvy-pzNIEGjNshxyYE8UG5aD2GDZbTbitHWiCujlXm8fj3abcewbyO7SyTlHQoZJTXTDKxJS0nKMt6u1~a6oWyZdzd8dE5wkFadCY76N1aH0Npu6fs3ymC5oLSpbFLhdXuNU2JGlDNOr0Ss8Ry9~PzLiaolRPxvUbnCaAZDms0k0d0N3gKAA__' alt="User profile" />
                            <div className="user-info">
                                <p>Jane Cooper</p>
                                <div className="categories">
                                    <span>Scam</span><span>Hate Speech</span><span>3R</span><span>+4</span>
                                </div>
                            </div>
                        </div>
                        <div className="right">
                            <p>Engagement</p>
                            <p>85%</p>
                        </div>
                    </GlobalInnerCard>
                    <div className="d-flex align-items-center justify-content-between numbers">
                        <GlobalInnerCard>
                            <p>Following</p>
                            <p>9M</p>
                        </GlobalInnerCard>
                        <GlobalInnerCard>
                            <p>Followers</p>
                            <p>9M</p>
                        </GlobalInnerCard>
                        <GlobalInnerCard>
                            <p>Posts</p>
                            <p>9M</p>
                        </GlobalInnerCard>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default ContentDetailsInfo