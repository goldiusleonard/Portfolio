import React from "react";
import PDFDetails from "../../components/PDF/PDFDetails";
import PDFCommentInfo from "../../components/PDF/PDFCommentInfo";
import PDFCommentTopCard from "../../components/PDF/PDFCommentTopCard";
import useApiData from "../../hooks/useApiData";
import endpoints from "../../config/config.dev";

function PDFCommentDetails() {
  // const { data, loadingData } = useApiData(`${endpoints.getContentDetail}?video_id=${content?.video_id}`, showMessage);

  return (
    <div className="pdf-content-details pdf-comment-details">
      <div className='content-details-stats'>
        <PDFCommentTopCard/>
        </div>
      <PDFDetails />
      <PDFCommentInfo />
    </div>
  );
}

export default PDFCommentDetails;
