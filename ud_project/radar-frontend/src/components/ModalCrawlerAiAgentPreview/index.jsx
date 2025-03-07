import React, { useEffect, useState } from "react";
import CustomModal from "../custom-modal/CustomModal";
import Button from "../button/Button";
import CrawlerAiAgentPreviewStep1 from "./CrawlerAiAgentPreviewStep1";
import CrawlerAiAgentPreviewStep2 from "./CrawlerAiAgentPreviewStep2";
import { CheckCircle } from "../../assets/icons";
import endpoints from "../../config/config.dev";
import axios from "axios";

// DO NOT DELETE: This is temporary Post Data
const analysisPostSample = {
  "files_names": [
    "Test_file.json",
    "test_file.v1.en.law_document"
  ],
  "category": "Scam",
  "subcategory": "Crypto",
  "risk_levels": {
    "High Risk": [
      "Promoting fraudulent Forex trading schemes, such as Ponzi schemes, pump-and-dump tactics, or any other investment opportunities that promise unrealistic returns with the intent to defraud individuals.",
      "Sharing fake or manipulated Forex market data with the purpose of misleading individuals into making trades, often to benefit the person sharing the data or cause harm to the trader."
    ],
    "Medium Risk": [
      "Offering questionable Forex trading advice or strategies without intent to defraud, such as promoting high-risk trades without proper risk management or sharing personal opinions without a solid financial basis.",
      "Discussing speculative Forex trading strategies or market predictions that are based on unverified information or personal guesses, which could mislead individuals into making poor financial decisions."
    ],
    "Low Risk": [
      "Discussing Forex as an investment option in neutral or educational contexts, such as explaining how Forex trading works, potential risks, or the mechanics of currency exchange markets.",
      "Sharing general, factual information about Forex trading, such as the role of central banks, interest rates, or geopolitical events in influencing currency prices, without promoting specific trading platforms or financial gains."
    ]
  },
  "post_date": {
    "start_date": "2024-01-22",
    "end_date": "2024-12-30"
  },
  "agent_builder_name": "agentname2"
}

//Props
// {
//   isShow: boolean
//   onClose: () => void
//   data: object represent by AgentDetails json on ../../data/AiBuilderData/crawlerAgentDetails.json
// }

const ModalCrawlerAiAgentPreview = ({ isShow, onClose, data, agentID }) => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [step, setStep] = useState(1);
  const [riskPriority, setRiskPriority] = useState({
    high: "",
    medium: "",
    low: "",
  });
  const [postDate, setPostDate] = useState({
    start_date: "",
    end_date: "",
  });
  const [fileName, setFileName] = useState("");

  const onChangeRiskPriority = (value, type) => {
    setRiskPriority((prevState) => ({ ...prevState, [type]: value }));
  };

  const onChangePostDate = (state) => setPostDate(state);

  const onChangeFileName = (state) => setFileName(state);

  const onNextStep = () => {
    if(step === 2){
      console.log(22)
      sentCrawlerPreviewAnalysis()
    }
    if (step === 3) return;
    console.log(step)
    setStep((prevState) => prevState + 1);
  };

  const sentCrawlerPreviewAnalysis = async () => {
		try {
			const response = await axios({
				method: 'post',
				url: endpoints.postCrawlerPreviewAnalysis,
				data: analysisPostSample,
			});
			console.log(JSON.stringify(response.data));
		} catch (error) {
			console.error(error);
		} finally {
			console.log("Done")
		}
	}

  useEffect(() => {
    if (step === 3) {
      setIsDialogOpen(true);
    }
  }, [step]);

  const onPrevStep = () => {
    if (step - 1 >= 1) {
      setStep((prevState) => prevState - 1);
    }
  };

  const handleClose = () => {
    setIsDialogOpen(false);
    setStep(1);
    onClose();
  };

  if (!isShow) return null;
  const content = (
    <div className="d-flex flex-column align-items-center justify-content-center">
      <img src={CheckCircle} alt="Check circle icon" />
      <p>AI Agent is Ready for Activation</p>
      <Button onClick={handleClose} text="Close" />
    </div>
  );
  const Content = () => {
    return (
      <div className="modal-crawler-ai-agent">
        {step === 1 ? (
          <CrawlerAiAgentPreviewStep1 data={data} agentID={agentID}/>
        ) : (
          <>
            <CrawlerAiAgentPreviewStep2
              category={data.category}
              subCategory={data.subcategory}
              riskPriorityOptions={data.analysis.risk_levels}
              fileNameOptions={data.analysis.files_name}
              riskPriority={riskPriority}
              postDate={postDate}
              fileName={fileName}
              onChangeRiskPriority={onChangeRiskPriority}
              onChangePostDate={onChangePostDate}
              onChangeFileName={onChangeFileName}
            />

            <CustomModal
              className="ai-agent-published"
              isOpen={isDialogOpen}
              title={"AI Agent Status"}
              content={content}
              size={"md"}
            />
          </>
        )}
      </div>
    );
  };

  const Footer = () => {
    return (
      <div className={`modal-crawler-ai-agent-footer`}>
        {step > 1 && (
          <Button variant="outline" text="Back" onClick={onPrevStep} />
        )}
        <div className="right-side justify-end">
          <Button variant="outline" text="Recrawler Agent" />
          <Button text="Next" onClick={onNextStep} />
        </div>
      </div>
    );
  };

  return (
    <CustomModal
      className="modal-crawler-ai-agent-custom-modal"
      isOpen={isShow}
      toggle={onClose}
      title={`Crawler AI Agent Preview ${step === 2 ? "( Analysis )" : ""}`}
      content={<Content />}
      footer={<Footer />}
    />
  );
};

export default ModalCrawlerAiAgentPreview;
