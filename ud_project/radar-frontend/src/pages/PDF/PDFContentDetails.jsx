import PDFCommentInfo from "../../components/PDF/PDFCommentInfo";
import PDFContentInfo from "../../components/PDF/PDFContentInfo";
import PDFDetails from "../../components/PDF/PDFDetails";

const PDFContentDetails = () => {

    return (
        <>
            
            <div className="pdf-content-details">
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
                <PDFDetails />
                <PDFContentInfo />
              
            </div>
        </>

    )
}

export default PDFContentDetails;