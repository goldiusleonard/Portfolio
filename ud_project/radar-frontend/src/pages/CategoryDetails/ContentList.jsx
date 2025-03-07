import React, { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import useApiData from "../../hooks/useApiData";
import Button from "../../components/ui/buttons/Button";
import Searchbar from "../../components/ui/inputs/Searchbar";
import Select from "../../components/Select/Select";
import { contentListHeaders } from "../../data/scammerRank";
import endpoints from "../../config/config.dev";
import axios from "axios";
import { FilterMatchMode } from "primereact/api";
import ReportContentConfirm from "./../../components/Modal/ReportContentConfirm";
import { ArrowRightIcon } from "../../assets/icons";
import CustomBtn from "../../components/button/Button";
import { getUserFromLocalStorage } from "../../Util";
import { useQuery } from "react-query";
import { useApiRequest } from "../../hooks/useApiRequest";
import { useGlobalData } from "../../App";

const riskLevel = ["Select Risk Level", "High", "Medium", "Low"];

const debounce = (func, delay = 500) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
      func(...args);
    }, delay);
  };
};

function ContentList({
  contentListUrl,
  scrollHeight,
  Table,
  totalCaseShow,
  aiAgentListHeaders,
  handleReportContents,
  saveStatehandler,
  viewAllContent,
  reported,
}) {
  const navigate = useNavigate();
const {apiRequest} = useApiRequest();
 const {AIAgentID} = useGlobalData();
  const [selectedContent, setSelectedContent] = useState([]);
  const [sendLoading, setSendLoading] = useState(false);
  const [openModal, setOpenModal] = useState(false);
  const user = getUserFromLocalStorage();

  const { data, isLoading} = useQuery({
    queryKey: ["ContentList", AIAgentID],
    queryFn: () => apiRequest("GET", contentListUrl),
  });
  

  const toggleModal = () => setOpenModal((prev) => !prev);
  const dataKeySample = data?.data?.map((item, index) => `${item.video_id}_${index}`);


  const handleSelectionChange = (row) => {
    setSelectedContent((prevSelectedContent) => {
      const isSelected = prevSelectedContent.includes(row);
      if (isSelected) {
        return prevSelectedContent.filter((item) => item !== row);
      } else {
        return [...prevSelectedContent, row];
      }
    });
  };

  const handleSelectAll = (selectAll) => {
    if (selectAll) {
      setSelectedContent(selectAll);
    } else {
      setSelectedContent([]);
    }
  };

  const [filters, setFilters] = useState({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
  });

  const sendReport = async () => {
    if (selectedContent.length > 0) {
      setSendLoading(true);
      toggleModal();
      try {
        const response = await axios.post(
          endpoints.postVideoContentReport,
          selectedContent
        );
        if (response) {
          handleReportContents("Contents has been successfully reported");
        }
        // refetch();
        setSelectedContent([]);
      } catch (error) {
        handleReportContents(
          "Failed to report contents. Please try again or check your connection"
        );
      } finally {
        setSendLoading(false);
      }
    }
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

  const handleRiskLevelChange = useCallback(
    (value) => {
      setFilters((prevFilters) => ({
        ...prevFilters,
        global: {
          ...prevFilters.global,
          status: value === "Select Risk Level" ? null : value,
        },
      }));
    },
    [setFilters]
  );

  const onRowDoubleClick = useCallback(
    (row) => {
      // Check the role before executing the callback logic
      // if (user.role === "SeniorLeader") {
      //   return;
      // }
      console.log("row", row);

      if (row.identification_id.endsWith("9396")) {
     navigate("/category-details/comment-details", { state: row });
      }
      else{
        navigate("/category-details/content-details", { state: row });
      }
   
      if (typeof saveStatehandler === "function") {
        saveStatehandler();
      }
    },
    [navigate, saveStatehandler, user.role]
  );

  const onGlobalFilterChangeDebounced = debounce(onGlobalFilterChange);

  return (
    <div className="h-100">
      <div className="content-list-wrapper-container justify-content-between d-flex">
        {totalCaseShow && (
          <div className="totalCase-wrapper me-3">
            <h6>{reported ? "Reported" : "Total"}</h6>
            <p>{data?.length ?? 0} Contents</p>
          </div>
        )}
        <Searchbar
          placeholder="Search Keyword"
          onChange={onGlobalFilterChangeDebounced}
        />
        {viewAllContent ? (
          <CustomBtn
            text={
              <>
                See All Content
                <span className="icon">
                  <ArrowRightIcon fill="#fff" />
                </span>
              </>
            }
            variant="all-content-button"
            onClick={() => navigate("/ai-agent/agent-details/all-contents")}
          />
        ) : (
          <Select
            options={riskLevel}
            defaultValue="Select Risk Level"
            placeholder="Select Risk Level"
            className="StatusDropdown"
            arrowSize="15"
            onChange={handleRiskLevelChange}
          />
        )}

        {!totalCaseShow && (
          <Button
            title="Report Selected"
            classNames={
              sendLoading || selectedContent.length === 0
                ? "report-btn-disabled"
                : "bulk-report-btn"
            }
            // onClick={sendReport}
            disabled={selectedContent.length === 0}
            onClick={toggleModal}
          />
        )}
      </div>
      <Table
        values={data?.data}
        filters={filters}
        dataKey={dataKeySample}
        // dataKey="global"
        headers={aiAgentListHeaders ?? contentListHeaders}
        scrollHeight={scrollHeight}
        withCheckbox={!totalCaseShow}
        onRowDoubleClick={onRowDoubleClick}
        onRowClick={handleSelectionChange}
        onSelectAll={handleSelectAll}
        selection={selectedContent}
        loading={isLoading}
      />

      <ReportContentConfirm
        isOpen={openModal}
        toggle={toggleModal}
        totalSelected={selectedContent.length}
        sendReport={sendReport}
      />
    </div>
  );
}

export default React.memo(ContentList, (prevProps, nextProps) => {
  return (
    prevProps.contentListUrl === nextProps.contentListUrl &&
    prevProps.scrollHeight === nextProps.scrollHeight
  );
});
