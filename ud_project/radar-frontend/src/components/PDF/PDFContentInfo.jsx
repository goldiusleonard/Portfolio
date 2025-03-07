import PDFGlobalCard from "./PDFGlobalCard";
import { vidThumbnail } from "../../assets/images";
import PDFTopComments from "./PDFTopComments";
import PDFJustification from "./PDFJustification";
import PDFTimeline from "./PDFTimeline";
import PDFKeywords from "./PDFKeywords";
import PDFHashtags from "./PDFHashtags";

const PDFContentInfo = () => {
    return (
        <div className="pdf-content-info">
            <PDFGlobalCard>
                <div className="video-details">
                    <div className="vid">
                        <img src={vidThumbnail} alt="Video thumbnail" />
                    </div>
                    <div className="content-url">
                        <p>Content URL</p>
                        <a href="https://www.tiktok.com/@zestie.my/video/7324646825175125249?q=Malaysia%20Salary&t=1734071955221">https://www.tiktok.com/@zestie.my/video/7324646825175125249?q=Malaysia%20Salary&t=1734071955221</a>
                    </div>
                    <div className="content-description">
                        <p>Content Description</p>
                        <p>How much salary is enough to live in KL? #learnontiktok #foryou #streetinterview #salary #career #urban #living #kualalumpur #malaysia #fyp #viral</p>
                    </div>
                </div>
                <PDFTopComments />
            </PDFGlobalCard>
            <PDFGlobalCard>
                <PDFJustification />
                <PDFTimeline />
                <PDFKeywords />
                <PDFHashtags />
            </PDFGlobalCard>
        </div>
    )
}

export default PDFContentInfo;