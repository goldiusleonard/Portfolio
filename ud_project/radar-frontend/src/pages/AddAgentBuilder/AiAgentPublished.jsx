import { CloseIcon } from "../../assets/icons"
import { useState } from "react"
import CustomModal from "../../components/custom-modal/CustomModal"
import { CheckCircle } from "../../assets/icons"
import Button from "../../components/button/Button"

const AiAgentPublished = ({ isOpen, toggle }) => {
    const handleCancel = () => {
        toggle(false); 
    };
    const titleContent = <div className="d-flex align-items-center justify-content-between">
        AI Agent Published
        <CloseIcon onClick={handleCancel} fill='#80EED3' />
    </div>

    const content = <div className="d-flex flex-column align-items-center justify-content-center">
        <img src={CheckCircle} alt="Check circle icon" />
        <p>AI Agent Published and can be seen by all officers.</p>
        <Button onClick={handleCancel} text='Close' />
    </div>

    return <CustomModal className='ai-agent-published' isOpen={isOpen} title={titleContent} content={content} centered  size="md" />
}

export default AiAgentPublished