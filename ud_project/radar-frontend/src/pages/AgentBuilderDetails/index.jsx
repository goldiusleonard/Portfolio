import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useGlobalData } from "../../App.js";
import DateRangePicker from "../../components/DatePicker/index";
import moment from "moment";
import UploadVideos from "../../components/UploadVideos";
import useBreadcrumb from "../../hooks/useBreadcrumb.js";
import ContentCategorySelection from "../../components/ContentCategorySelection";
import Table from "../../components/tables/BootstrapTable";
import endpoints from "../../config/config.dev";
import ContentList from "../CategoryDetails/ContentList";
import { aiAgentListHeaders } from "../../data/scammerRank";
import { useStatus } from "../../contexts/StatusContext.js";
import DeactivateModal from "../../components/DeactivateModal";
import ActivateAgentModal from "../../components/Modal/ActivateAgentModal";
import UploadedDocuments from "../../components/uploadedDocuments/UploadedDocuments";
import KeywordListNotEditable from "../../components/KeywordList/KeywordListNotEditable.jsx";
import AiAgentPublished from "../AddAgentBuilder/AiAgentPublished.jsx";
import { getUserFromLocalStorage } from "../../Util/index";
import "./AgentBuilderDetails.scss";
import AgentDetails from "../../data/sampleJson/AgentDetails.json";
import { queryClient, useApiRequest } from "../../hooks/useApiRequest.js";
import { useQuery, useMutation } from "react-query";
import LoaderAnimation from "../../components/LoaderAnimation/index.jsx";

const AgentBuilderDetails = () => {
  const { agentID } = useParams();
  const {apiRequest} = useApiRequest()
  const { setAIAgentID } = useGlobalData();
  const user = getUserFromLocalStorage();
  const ref = React.useRef(null);
  const scrollHeight = ref.current?.offsetHeight - 120;
  const navigate = useNavigate();
  const { isAgentActive, setIsAgentActive } = useStatus();
  const contentListUrl = `${endpoints.getAgentList}${agentID}/content-list`;
  const [isAgentOutput, setIsAgentOutput] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [activateModalOpen, setActivateModalOpen] = useState(false);
  const [showEditableScreen, setShowEditableScreen] = useState(false);
  const [publishModalOpen, setPublishModalOpen] = useState(false);
  const [isAIAgentPublished, setIsAIAgentPublished] = useState();
  const title = "AI Agent > Agent Details";
  const hasBackButton = true;
  const hasDateFilter = false;

  useBreadcrumb({ title, hasBackButton, hasDateFilter });

  const { data, isLoading} = useQuery({
    queryKey: ["agentDetails", agentID],
    queryFn: () => apiRequest("GET", `${endpoints.getAgentList}${agentID}`),
  });


  const agentName = data?.agentName || "agent name";
  const category = data?.category || "scam";
  const subcategory = data?.subcategory || "Sample Agent subcategory";
  const crawlingPeriod = data?.crawlingPeriod || "Sample crawling period";
  const createdBy = data?.createdBy || "user name";
  const createdTime = data?.createdTime || "01.01.2015";
  const description = data?.description || "Sample Agent description";
  const isPublished = data?.isPublished || false;
  const keywordList = data?.keywordList || [];
  const usernameList = data?.usernameList || [];
  const legalDocuments = data?.legalDocuments || [];
  const isKEywordCrawler = data?.isKEywordCrawler || true;
  const isUsernameCrawler = data?.isUsernameCrawler || false;
  const crawlingEndDate = data?.crawlingEndDate || "01.01.2015";
  const crawlingStartDate = data?.crawlingStartDate || "01.01.2015";
  const isPublishedUrl = `${endpoints.getAgentList}${agentID}/is-published?is_published=true`;
  const changeStatusUrl = `${endpoints.getAgentList}${agentID}/status?status=Ready`;

  useEffect(() => {
    setAIAgentID(agentID);
  }, [agentID, setAIAgentID]);

  const { mutate} = useMutation({
    mutationFn: () => apiRequest("PATCH", isPublishedUrl),
    onSuccess: () => {
      queryClient.invalidateQueries("agentDetails");
      setPublishModalOpen(true);
      setIsAIAgentPublished(true);
    },
  })

  const {mutate: changeStatus} = useMutation({
    mutationFn: () => apiRequest("PATCH", changeStatusUrl),
    
  })

  useEffect(() => {
    if (data?.isPublished !== undefined) {
      setIsAIAgentPublished(data.isPublished);
    }
  }, [data]);
  const handlePublish = () => {
   mutate({id: agentID})
  };

    const handleEdit = () => {
    navigate("/ai-agent/add-agent/", {
      state: { showEditableScreen: true, data: data },
    });
  };

   const toggleModal = () => {
    setModalOpen(!modalOpen);
  };

  const toggleActivateModal = () => {
    setIsAgentActive(true);
    setActivateModalOpen(!activateModalOpen);
    changeStatus({id: agentID})
  };

  return (
    <div className="builder-page-wrapper">
      <section className="agent-details">
        <div className="details-wrapper">
          <div className="details-wrapper-inside card-wrap me-3">
            <div className="content-details-cards">
              <div className="content-details-cards-title">Agent Name</div>
              <div className="content-details-cards-content">{agentName}</div>
            </div>
            <div className="content-details-cards">
              <div className="content-details-cards-title">Created by</div>
              <div className="content-details-cards-content">{createdBy}</div>
            </div>
            <div className="content-details-cards">
              <div className="content-details-cards-title">Created Time</div>
              <div className="content-details-cards-content">{createdTime}</div>
            </div>
            <div className="content-details-cards">
              <div className="content-details-cards-title">Description</div>
              <div className="">{description}</div>
            </div>
          </div>
          {user.role !== "Officer" && (
            <div className="action-btn-container ">
              <div className="grid-item-1">
                <button
                  className="btn-action btn-modify mb-2"
                  onClick={handleEdit}
                >
                  Edit AI Agent
                </button>
                {isAgentActive ? (
                  <button
                    className="btn-action btn-deactivate grid-item-2"
                    onClick={toggleModal}
                  >
                    Deactivate
                  </button>
                ) : (
                  <button
                    className="btn-action  btn-modify"
                    onClick={toggleActivateModal}
                  >
                    Activate
                  </button>
                )}
              </div>

              <div className="grid-item-3 ">
                {" "}
                <button
                  className="publish-btn"
                  onClick={handlePublish}
                  disabled={isAIAgentPublished}
                >
                  Publish
                </button>
              </div>
            </div>
          )}
        </div>
      </section>
      <section className="selection-wrapper d-flex ">
        <div className="content-category-selection">
          <div className=" card-wrap h-50">
            <ContentCategorySelection
              isAgentOutput={isAgentOutput}
              showEditableScreen={showEditableScreen}
              category={category}
              subcategory={subcategory}
              crawlingEndDate={crawlingEndDate}
              crawlingStartDate={crawlingStartDate}
            />
          </div>
          <div className=" card-wrap mt-3 bottom-card-wrap">
            <UploadedDocuments legalDocument={legalDocuments} />
          </div>
        </div>
        <div className="d-flex flex-grow-1 flex-column video-upload-container ms-3">
          <KeywordListNotEditable
            keywordList={keywordList}
            isKEywordCrawler={isKEywordCrawler}
            isUsernameCrawler={isUsernameCrawler}
          />
        </div>
      </section>
      <section
        className="parameter-output-wrapper card-wrap position-relative"
        ref={ref}
      >
        <ContentList
          contentListUrl={contentListUrl}
          scrollHeight={scrollHeight}
          Table={Table}
          totalCaseShow={true}
          aiAgentListHeaders={aiAgentListHeaders}
          viewAllContent={true}
        />
      </section>

      <DeactivateModal isOpen={modalOpen} toggle={toggleModal} />
      <ActivateAgentModal
        isOpen={activateModalOpen}
        toggle={toggleActivateModal}
      />
      <AiAgentPublished
        isOpen={publishModalOpen}
        toggle={setPublishModalOpen}
      />
    </div>
  );
};

export default AgentBuilderDetails;
