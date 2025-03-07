import PDFGlobalCard from "./PDFGlobalCard";
import PDFTopComments from "./PDFTopComments";
import PDFJustification from "./PDFJustification";
import PDFTimeline from "./PDFTimeline";
import PDFKeywords from "./PDFKeywords";
import PDFHashtags from "./PDFHashtags";
import SampleCommentScreenshot from "../../assets/images/sample-comment-screenshot.png";

const PDFCommentInfo = () => {
  return (
    <div className="pdf-content-info">
      <PDFGlobalCard>
        <div className="screenshot-container">
          <img
            src={SampleCommentScreenshot}
            alt="comment screenshot"
            className="comment-screenshot"
          />
        </div>
        <div className="content-url">
          <p>Content URL</p>
          <a href="https://www.tiktok.com/@zestie.my/video/7324646825175125249?q=Malaysia%20Salary&t=1734071955221">
            https://www.tiktok.com/@zestie.my/video/7324646825175125249?q=Malaysia%20Salary&t=1734071955221
          </a>
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
  );
};

export default PDFCommentInfo;
