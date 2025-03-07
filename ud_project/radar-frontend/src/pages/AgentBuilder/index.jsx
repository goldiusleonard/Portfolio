import React, { useState, useTransition, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import Searchbar from "../../components/ui/inputs/Searchbar";
import Table from "../../components/tables/Table";
import { AiAgentList } from "../../data/scammerRank";
import { FilterMatchMode, FilterOperator } from "primereact/api";
import CustomModal from "../../components/custom-modal/CustomModal";
import ReviewStatus from "./ReviewStatus";
import useBreadcrumb from "../../hooks/useBreadcrumb";
import { getUserFromLocalStorage } from "../../Util/index";
import crawlerAgentDetailsJson from "../../data/AiBuilderData/crawlerAgentDetails.json";
import ModalCrawlerAiAgentPreview from "../../components/ModalCrawlerAiAgentPreview";
import LoaderAnimation from "../../components/LoaderAnimation";
import { useQuery, useMutation } from "react-query";
import { useApiRequest } from "../../hooks/useApiRequest";
import endpoints from "../../config/config.dev";
import { useGlobalData } from "../../App";

// const listStatus =['AI Agent Name','Created by','Created Time','Validity Period' ]
const listStatus = ["All", "Crawling", "Review", "Ready"];
export const AiAgentListHeader = [
  { field: "agentName", header: "AI Agent Name" },
  { field: "createdBy", header: "Created by" },
  { field: "createdTime", header: "Created on" },
  { field: "category", header: "Category" },
  { field: "subcategory", header: "Subcategory" },
  { field: "crawlingPeriod", header: "Crawling Period" },
  { field: "status", header: "Status" },
];

const title = "AI Agent Builder";
const hasBackButton = false;
const hasDateFilter = false;
const hasCategoryFilter = false;

const AgentBuilder = () => {
  const navigate = useNavigate();
  const { apiRequest } = useApiRequest();
  const { setAIAgentID, AIAgentID} = useGlobalData();
  const [isPending, startTransition] = useTransition();
  const [activeStatus, setActiveStatus] = useState(listStatus[0]);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const user = getUserFromLocalStorage();
  useBreadcrumb({ title, hasBackButton, hasDateFilter, hasCategoryFilter });
  const toggleReviewModal = () => setIsReviewModalOpen((prev) => !prev);
  const [filters, setFilters] = useState({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
  });

  
  const { data, isLoading} = useQuery({
    queryKey: ["agentList"],
    queryFn: () => apiRequest("GET", endpoints.getAgentList),
  });


  const debounce = (func, delay = 500) => {
    let timeoutId;
    return (...args) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        func(...args);
      }, delay);
    };
  };

  const onGlobalFilterChange = useCallback(
    (e) => {
      const value = e.target.value;
      setFilters((prevFilters) => ({
        ...prevFilters,
        global: { ...prevFilters.global, value },
      }));
    },
    [setFilters]
  );

  const onGlobalFilterChangeDebounced = debounce(onGlobalFilterChange);

  // const changeStatusUrl = `${endpoints.getAgentList}/6/status?status=Ready`;
  const changeStatusUrl = `${endpoints.getAgentList}${AIAgentID}/status?status=Ready`;
  const {mutate: changeStatus} = useMutation({
      mutationFn: () => apiRequest("PATCH", changeStatusUrl),
      
    })

    const test = () => {
      if (AIAgentID) {
        changeStatus({id: AIAgentID})
      }
    }

  const handleRowClick = (e) => {
    const { status, agentID } = e.data;
    setAIAgentID(agentID);
    if (status !== "Crawling" && status !== "Review") {
      navigate(`/ai-agent/agent-details/${agentID}`);
      // navigate(`/ai-agent/agent-details`);
    } else if (status === "Review" && user.role !== "Officer") {
      ///show the modal of ai-agent-preview
      toggleReviewModal();
    } else if (status === "Crawling") {
      //do nothing
      // test()
      return;
    }
  };

  const statusFilterHandler = (e) => {
    const value = e.target.value;

    if (value === "0") {
      setActiveStatus(listStatus[value]);
      setFilters((prevFilters) => ({
        ...prevFilters,
        global: { ...prevFilters.global, value: null },
      }));
      return;
    } else {
      startTransition(() => {
        setActiveStatus(listStatus[value]);
        setFilters((prevFilters) => ({
          global: { ...prevFilters.global, value: listStatus[value] },
        }));
      });
    }
  };

  return (
    <div className="agent-builder-wrapper card-wrap">
      <section className="upper-section ">
        <Searchbar
          placeholder="Search"
          onChange={onGlobalFilterChangeDebounced}
        />
        {user.role === "SeniorLeader" && <AddAiAgentBtn />}
      </section>
      {user.role !== "Officer" && (
        <section className="buttons-container">
          {listStatus.map((item, index) => {
            const style = `filter-button ${
              activeStatus === item && !isPending && "active"
            }`;

            return (
              <button
                key={index}
                className={style}
                onClick={statusFilterHandler}
                value={index}
              >
                {item}
              </button>
            );
          })}
        </section>
      )}

      {isLoading ? (
        <LoaderAnimation />
      ) : (
        <section className="table-sec">
          <Table
            // values={AiAgentList}
            values={data}
            filters={filters}
            dataKey="global"
            headers={AiAgentListHeader}
            // scrollHeight={scrollHeight}
            // withCheckbox
            // onRowDoubleClick={onClickOfRowContent}
            onRowClick={handleRowClick}
            // onSelectionChange={handleonSelectionChange}
            // selection={selectedContent}
            loading={false}
            role={user.role}
            emptyMessage={EmptyScreen}
            // tableClassName='tableContainer'
          />
        </section>
      )}

      <ModalCrawlerAiAgentPreview
        isShow={isReviewModalOpen}
        onClose={toggleReviewModal}
        data={crawlerAgentDetailsJson}
        agentID={AIAgentID}
      />
    </div>
  );
};

export default AgentBuilder;

function EmptyScreen() {
  return (
    <div className="ai-agent-empty">
      <p>There is no AI Agent available, create a new AI agent to start.</p>
      <AddAiAgentBtn />
    </div>
  );
}

const AddAiAgentBtn = () => {
  const navigate = useNavigate();

  return (
    <button
      className="addAgent_btn"
      onClick={() => navigate("/ai-agent/add-agent")}
    >
      <span>+</span>Add AI Agent
    </button>
  );
};

const ReviewFinishButton = () => <button className="review-btn">Finish</button>;
