import React from "react";
import { useParams } from "react-router-dom";
import ContentList from "../../pages/CategoryDetails/ContentList";
import Table from "../tables/BootstrapTable";
import { aiAgentListHeaders } from "../../data/scammerRank";
import endpoints from "../../config/config.dev";
import useBreadcrumb from "../../hooks/useBreadcrumb";
import { useGlobalData } from "../../App";
import { use } from "react";

const Contents = () => {
 const {AIAgentID} = useGlobalData();
  const contentListUrl = `${endpoints.getAgentList}${AIAgentID}/content-list`;
  const ref = React.useRef(null);
  const scrollHeight = ref.current?.offsetHeight - 120;
  const title = "";
  const hasBackButton = true;
  const hasDateFilter = false;
 
  useBreadcrumb({ title, hasBackButton, hasDateFilter });
console.log("id in contents", AIAgentID);




  return (
    <div className="contents-wrapper h-100 w-100">
      <ContentList
        contentListUrl={contentListUrl}
        scrollHeight={scrollHeight}
        Table={Table}
        totalCaseShow={true}
        aiAgentListHeaders={aiAgentListHeaders}
        reported={true}
      />
    </div>
  );
};

export default Contents;
