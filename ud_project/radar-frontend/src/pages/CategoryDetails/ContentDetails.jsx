import { ArrowRight } from "../../assets/icons"
import { useState } from "react"
import ContentDetailsInfo from "./ContentDetailsInfo"

const ContentDetails = ({setIsContentDetail}) => {
    const [currentOption, setCurrentOption] = useState('content-detail')

    return (
        <div className="direct-link-content-details"> 
            <div className="top">
                <img onClick={() => setIsContentDetail(false)} src={ArrowRight} alt="Arrow right icon" />
                <nav aria-label="Breadcrumb">
                    <ol>
                        <li>Generate Content</li>
                        <li>Content Detail</li>
                    </ol>
                </nav>
            </div>
            <div className="direct-link-content-details-tabs">
                <div onClick={() => setCurrentOption('content-detail')} className={`single-tab ${currentOption === 'content-detail' && 'active'}`}>Content Detail</div>
                <div onClick={() => setCurrentOption('standard-regulations')} className={`single-tab ${currentOption === 'standard-regulations' && 'active'}`}>Standard & Regulations</div>
            </div>
            {currentOption === 'content-detail' && <ContentDetailsInfo />}
        </div>
    )
}

export default ContentDetails