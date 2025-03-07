import { ArrowRight } from "../../assets/icons"
import Button from "../../components/button/Button"
import GlobalInnerCard from "./GlobalInnerCard"
import HeatMap from "../../components/HeatMap"
import creatorData from '../../pages/CreatorScreen/CreatorScreen.json'
import { useState } from "react"

const ProfileDetails = ({setIsContentDetail}) => {
    const [highlightedContent, setHighlightedContent] = useState([])

    const handleHighlightedContent = (content) => {
        setHighlightedContent(content);
      };

    return (
        <div className="direct-link-content-details"> 
            <div className="top">
                <img onClick={() => setIsContentDetail(false)} src={ArrowRight} alt="Arrow right icon" />
                <nav aria-label="Breadcrumb">
                    <ol>
                        <li>Generate Content</li>
                        <li>Creator Detail</li>
                    </ol>
                </nav>
            </div>
            <div className="creator-info">
                <GlobalInnerCard>
                    <div className="d-flex align-items-center justify-content-between">
                        <div className="left">
                            <img src='https://s3-alpha-sig.figma.com/img/78d9/96ec/fa1be286e3b17627a17bbb20e41bbdc5?Expires=1735516800&Key-Pair-Id=APKAQ4GOSFWCVNEHN3O4&Signature=MALGNpki0oUdLWg5nkdne~ntnTsWOHL3RQp7YypAWM5NtvuMFnNVGGmjFTtQIjwwUqayB2SEGa79wTsocMREeO6ypDnYUPIVUYfUBdYXILd9k0Gqcj4mjn04vMubq0ckA5jy8rvWieuBMno-O0M3fr7dwPoFvoTdlUZvy-pzNIEGjNshxyYE8UG5aD2GDZbTbitHWiCujlXm8fj3abcewbyO7SyTlHQoZJTXTDKxJS0nKMt6u1~a6oWyZdzd8dE5wkFadCY76N1aH0Npu6fs3ymC5oLSpbFLhdXuNU2JGlDNOr0Ss8Ry9~PzLiaolRPxvUbnCaAZDms0k0d0N3gKAA__' alt="User profile" />
                            <div className="user-info">
                                <p>#1 Jane Cooper</p>
                                <div className="categories">
                                    <span>Scam</span><span>Hate Speech</span><span>3R</span><span>+4</span>
                                </div>
                            </div>
                        </div>
                        <div className="right">
                            <Button className='outline' text={
                                <div className="d-flex align-items-center">
                                    View Profile Details
                                    <img src={ArrowRight} alt="Arrow right icon" />
                                </div>
                            } />
                        </div>
                    </div>
                    <div className="d-flex align-items-center mt-3">
                        <div className='content-details-cards'>
                            <div className='content-details-cards-title'>Following</div>
                            <div className='content-details-cards-content'>9M</div>
                        </div>
                        <div className='content-details-cards'>
                            <div className='content-details-cards-title'>Followers</div>
                            <div className='content-details-cards-content'>908</div>
                        </div>
                        <div className='content-details-cards'>
                            <div className='content-details-cards-title'>Posts</div>
                            <div className='content-details-cards-content'>789</div>
                        </div>
                        <div className='content-details-cards'>
                            <div className='content-details-cards-title'>Engagement</div>
                            <div className='content-details-cards-content'>85%</div>
                        </div>
                        <div className='content-details-cards'>
                            <div className='content-details-cards-title'>Last Post Date</div>
                            <div className='content-details-cards-content risk high'>30 May 24</div>
                        </div>
                    </div>
                </GlobalInnerCard>
                <div className="d-flex align-items-center visuals">
                    <div className="category-post-status">Category post status</div>
                    <div className="heatmap-container">
                        <HeatMap data={creatorData.profiles[0].threats} setHighlightedContent={handleHighlightedContent} />
                    </div>
                </div>
            </div>
            
        </div>
    )
}

export default ProfileDetails