import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import DateRangePicker from "../../components/DatePicker/index";
import moment from "moment";
import SocialMediaSelection from "../../components/SocialMediaSelection";
import arrowDown from "../../assets/icons/select_arrow.svg";
import aiIncon from "../../assets/icons/ai_star_icon.svg";
import Select from "../../components/Select/Select";
import endpoints from "../../config/config.dev";
import editIcon from "../../assets/icons/pen.svg";
import DeactivateModal from "../../components/DeactivateModal";
import ActivateAgentModal from "../../components/Modal/ActivateAgentModal";
import VerificationModal from "../../components/Modal/VerificationModal";
import GenerateByURL from "../../components/GenerateByURL";
import EditableParameters from "../../components/EditableParameters";
import "./AddAgentBuilder.scss";
// import data from "./data.json";
import KeywordSection from "./KeywordSection";
import CatSubcatSelection from "../../components/CatSubcatSelection";
import useBreadcrumb from "../../hooks/useBreadcrumb";
import { useMutation } from "react-query";
import { useApiRequest } from "../../hooks/useApiRequest";
import { useGlobalData } from "../../App";

const initialValue = {
  "agentName": "",
  "agentID": null,
  "createdBy": "",
  "createdTime": "",
  "description": "",
  "category": "",
  "subcategory": "",
  "crawlingStartDate": "",
  "crawlingEndDate": "",
  "legalDocuments": [],
  "URLList": [],
  "socialMediaList": [],
  "isPublished": false,
  "isUsernameCrawler": true,
  "isKeywordCrawler": false,
  "usernameList": [],
  "keywordList": []
}

const AddAgentBuilder = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {apiRequest} = useApiRequest()
  const { showEditableScreen , data } = location.state || {};
  const [showDates, setShowDates] = useState(false);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
const {setUpdatedAgentData} = useGlobalData();
  const [modalOpen, setModalOpen] = useState(false);
  const [activateModalOpen, setActivateModalOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [agentName, setAgentName] = useState(data?.agentName || "agent name");
  const [description, setDescription] = useState(data?.description || "-");
  const [keywords, setKeywords] = useState(data?.keywordList || []);
  const [usernames, setUsernames] = useState(data?.usernameList || []);
  const isUsernameCrawler = data?.isUsernameCrawler || true;
const isKeywordCrawler = data?.isKeywordCrawler || true;
const [editedAgentData, setEditedAgentData] = useState(data || initialValue)

  const title = "AI Agent > Add Agent Builder";
  const hasBackButton = true;
  const hasDateFilter = false;

  useBreadcrumb({ title, hasBackButton, hasDateFilter });
  
const agentID = data?.agentID
const updateAgentUrl = `${endpoints.updateAgent}${agentID}`
const {mutate} = useMutation({ 
  mutationFn: (editedAgentData) => {
    return apiRequest("PUT", updateAgentUrl, editedAgentData)
  }
 })

  const toggleModal = () => {
    setModalOpen(!modalOpen);
  };

  const toggleActivateModal = () => {
    setActivateModalOpen(!activateModalOpen);
  };

  const handleStartDate = (date) => {
    setStartDate(date);
  };

  const handleDateToggle = () => {
    setShowDates(!showDates);
  };

  const handleEndDate = (date) => {
    setEndDate(date);
  };

  const handleEditClick = () => {
    setIsEditing(true);
  };

  const handleInputChange = (e) => {
    if (e.target.name === "agentName") {
      setAgentName(e.target.value);
      setEditedAgentData((prev) => ({ ...prev, agentName: e.target.value}));
     
    } else if (e.target.name === "description") {
      setDescription(e.target.value);
      setEditedAgentData((prev) => ({ ...prev, description: e.target.value }));
    }
  };

  const handleSave = () => {
    setIsEditing(false);
    if (data) {
      mutate(editedAgentData);
    }
    setUpdatedAgentData(editedAgentData);
    navigate("/ai-agent");
  };

  return (
    <div className="add-builder-page-wrapper">
      <section className="agent-details">
        <div className="details-wrapper card-wrap">
          <div className="content-details-cards">
            <div className="content-details-cards-title">Agent Name</div>
            <div className="content-details-cards-content">
              {isEditing ? (
                <input
                  type="text"
                  name="agentName"
                  value={agentName}
                  onChange={handleInputChange}
                />
              ) : (
                agentName
              )}
            </div>
          </div>
          <div className="content-details-cards">
            <div className="content-details-cards-title">Created by</div>
            <div className="content-details-cards-content">{data?.createdBy}</div>
          </div>
          <div className="content-details-cards">
            <div className="content-details-cards-title">Created Time</div>
            <div className="content-details-cards-content">{data?.createdTime}</div>
          </div>
          <div className="content-details-cards agent-description">
            <div className="content-details-cards-title">Description</div>
            <div className="content-details-cards-content">
              {isEditing ? (
                <input
                  type="text"
                  name="description"
                  value={description}
                  onChange={handleInputChange}
                />
              ) : (
                description
              )}
            </div>
          </div>
          {!isEditing && (
            <img
              src={editIcon}
              alt="edit icon"
              className="agent-edit-icon"
              onClick={handleEditClick}
            />
          )}
        </div>

        <button className="btn-action" onClick={handleSave}>
          Start Building
        </button>
      </section>
      <section className="create-selection-wrapper selection-wrapper">
        <div className="left-align">
          <div className="content-category-selection card-wrap">
            <CatSubcatSelection showEditableScreen={showEditableScreen} 
            agentCategory={data?.category} agentSubcategory={data?.subcategory} 
            setEditedAgentData={setEditedAgentData} editedAgentData={editedAgentData}
            />
          </div>
          <div className="upload-video-wrapper card-wrap mt-3">
            <SocialMediaSelection />
          </div>
          <div className="generate-by-url card-wrap">
            <GenerateByURL URLList={data?.URLList}  setEditedAgentData={setEditedAgentData} editedAgentData={editedAgentData}/>
          </div>
        </div>
        <KeywordSection
        setEditedAgentData={setEditedAgentData}
          startDate={startDate}
      
          endDate={endDate}
          keywords={keywords}
          usernames={usernames}
          isUsernameCrawler={isUsernameCrawler}
          isKeywordCrawler={isKeywordCrawler}
          onChangeStartDate={handleStartDate}
          onChangeEndDate={handleEndDate}
          onChangeKeywords={(v) => setKeywords(v)}
          onChangeUsernames={(v) => setUsernames(v)}
          showEditableScreen={showEditableScreen}
        />
      </section>

      <ActivateAgentModal
        isOpen={activateModalOpen}
        toggle={toggleActivateModal}
      />
    </div>
  );
};

export default AddAgentBuilder;
