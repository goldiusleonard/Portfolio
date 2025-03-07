import PDFGlobalCard from "./PDFGlobalCard";
import GlobalInnerCard from "../../pages/CategoryDetails/GlobalInnerCard";

const PDFDetails = () => {
    return (
        <div className="pdf-details">
            <PDFGlobalCard>
                <div className="items">
                    <div className="item">
                        <p>Category</p>
                        <p>Scam</p>
                    </div>
                    <div className="item">
                        <p>Sub-Category</p>
                        <p>Misinformation</p>
                    </div>
                    <div className="item">
                        <p>Topic</p>
                        <p>Salary</p>
                    </div>
                </div>
            </PDFGlobalCard>

            <PDFGlobalCard>
                <div className="outer-card">
                    <p className="card-title">Posted By</p>
                    <GlobalInnerCard>
                        <div className="left">
                            <img src='https://cdn-icons-png.flaticon.com/512/10337/10337609.png' alt="User profile" />
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
            </PDFGlobalCard>
        </div>
    )
}

export default PDFDetails;