import { PlusIcon, SearchIcon } from "../../assets/icons";
import Button from "../../components/button/Button";
import CustomModal from "../../components/custom-modal/CustomModal";
import DirectAttachAnalysisTable from "../CategoryDetails/DirectAttachAnalysisTable";
import { useState, useRef } from "react";
import { ContentCopy, Upload, Minus, CloseIcon } from "../../assets/icons";
import DirectLinkLoading from "../CategoryDetails/DirectLinkLoading";
import MinimizedProcess from "../CategoryDetails/MinimizedProcess";
import Select from "../../components/Select/Select";
import { FilterMatchMode } from "primereact/api";
import Alert from "../../components/Alert";
import useBreadcrumb from "../../hooks/useBreadcrumb";
import useApiData from "../../hooks/useApiData";
import endpoints from "../../config/config.dev";
import LoaderGif from "../../assets/images/loader.gif";
import axios from "axios";

const DirectLinkAnalysis = () => {
  const [isAttachOpen, setIsAttachOpen] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [isValid, setIsValid] = useState(null);
  const [isActive, setIsActive] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [uploadedData, setUploadedData] = useState([]);

  const inputRef = useRef(null);
  const [filters, setFilters] = useState({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
  });
  const [showMessage, setShowMessage] = useState(false);
useBreadcrumb({
  title: "",
  hasBackButton: false,
  hasDateFilter: true,
  hasCategoryFilter: true,
});

  const { data: tableData, loadingData: tableDataLoading, error: tableDataError } = useApiData(endpoints.getDirectLinkTableData);

  // const tikTokRegex =
  //   /^https?:\/\/(www\.)?tiktok\.com\/(@[A-Za-z0-9_.-]+\/video\/\d+|.+)$/;

  const tikTokRegex = /^https?:\/\/([a-z]+\.)?tiktok\.com(\/.*)?$/;



  const handleOpenAttachLink = () => {
    setIsAttachOpen(true);
    setShowMessage(false);
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setInputValue(value);
    setIsActive(value.length > 0);

    // Regex to validate TikTok URL
    setIsValid(tikTokRegex.test(value));
  };

  const sendLinkUrl = async () => {
    const user = localStorage.getItem('user');

    setIsLoading(true);
    try {
      const response = await axios.post(endpoints.postDirectLinkUrl, {urls: [inputValue]}, {
        headers: {
          Authorization: `Bearer ${JSON.parse(user)?.access_token}`
        }
      })

      const response2 = await axios.get(`/data.json`)
      console.log(response2);
      
      // const response2 = await axios.get(`${endpoints.getAgentContentList}/${response.data.agent_name}`, {
      //   headers: {
      //     Authorization: `Bearer ${JSON.parse(user)?.access_token}`
      //   }
      // })
      console.log('response 2', response2.data);
      
      setUploadedData(response2.data);
      console.log('upooled data', uploadedData);
      
    } catch(err) {
      console.log(err);
    } finally {
      setIsLoading(false);
      setIsSubmitted(true);console.log("Input Value:", inputValue);
    }
  }

  const handlePaste = () => {
    // const initialData = {
    //   // img: 'https://s3-alpha-sig.figma.com/img/8a2e/41b2/15428d3ee5ffe4e3ae87b9e741d9a38d?Expires=1734912000&Key-Pair-Id=APKAQ4GOSFWCVNEHN3O4&Signature=i7bR7e314l3gkvezDiCxXt3VJLY1LqRy9QQEJNIHW-bBtbDhCCswWpyLdNY-W3nqFQ5NAicFveZSeyWs3~pPQSc7YOu9-0NA8t1dHTxa1U-VpaD1vu4VkffvII5MCA-FrgtRdcwaIri4h91MvQugvMpNm2HUG1TMA-PLownZzUfBEvhlvSY-t7X7jRN-X6-ncewn~PoNIWYW5zHy8G6gZ-LRdRSSwB9IrXGj9TFn58dgVGqtkKEBA03soHJLn5y3bWYTkgLPgszZCmnXKfncKR5JWNqE3~1IV7DE7y3sFYJaUOg0UA1Km9GcGHIX5CcvCbuaK0ddmGxP9r24zpTrIg__',
    //   id: "FB240228CBMM000030",
    //   date: "17:20 - 11/10/24",
    //   socialMedia: "-",
    //   risk: "high",
    //   status: "Progress (70%)",
    //   topic: "-",
    // };

    sendLinkUrl()


    // setUploadedData((prevState) => [...prevState, initialData]);
    // setIsLoading(true);

    // setTimeout(() => {
    //   // setIsLoading(false);
    //   setIsSubmitted(true);
    //   setUploadedData((prevState) =>
    //     prevState.map((item) =>
    //       item.id === initialData.id
    //         ? {
    //             ...item,
    //             socialMedia: "Facebook",
    //             status: "Completed",
    //             topic: "Cryptocurrency",
    //           }
    //         : item
    //     )
    //   );
    // }, 3000);
  };

  const showContentDetails = () => {
    setIsSubmitted(true);
    setIsAttachOpen(true);
  };

  const handleCancel = () => {
    setIsAttachOpen(false);
    setIsSubmitted(false);
    setInputValue("");
    setIsActive(false);
    setIsValid(null);
    inputRef.current = "";
    setIsMinimized(false);
  };

  const handleMinimize = () => {
    setIsAttachOpen(false);
    setIsMinimized(true);
  };

  // Function to handle the button click
  const handlePasteLink = async () => {
    try {
      // Access the content from the clipboard
      const text = await navigator.clipboard.readText();
      if (inputRef.current) {
        inputRef.current.value = text; // Set the value of the input field
        inputRef.current.focus();
        setIsActive(text.length > 0);
        setInputValue(text);
        setIsValid(tikTokRegex.test(text));
      }
    } catch (error) {
      console.error("Failed to read clipboard contents: ", error);
    }
  };

  const handleReport = () => {
    setShowMessage(true);
    handleCancel();
  };

  const popupTableData = [
    {
      content: {
        thumbnail:
          "https://s3-alpha-sig.figma.com/img/8a2e/41b2/15428d3ee5ffe4e3ae87b9e741d9a38d?Expires=1734912000&Key-Pair-Id=APKAQ4GOSFWCVNEHN3O4&Signature=i7bR7e314l3gkvezDiCxXt3VJLY1LqRy9QQEJNIHW-bBtbDhCCswWpyLdNY-W3nqFQ5NAicFveZSeyWs3~pPQSc7YOu9-0NA8t1dHTxa1U-VpaD1vu4VkffvII5MCA-FrgtRdcwaIri4h91MvQugvMpNm2HUG1TMA-PLownZzUfBEvhlvSY-t7X7jRN-X6-ncewn~PoNIWYW5zHy8G6gZ-LRdRSSwB9IrXGj9TFn58dgVGqtkKEBA03soHJLn5y3bWYTkgLPgszZCmnXKfncKR5JWNqE3~1IV7DE7y3sFYJaUOg0UA1Km9GcGHIX5CcvCbuaK0ddmGxP9r24zpTrIg__",
        id: "FB240228CBMM000030",
        socialLink: "https://www.facebook.com/video/?fbid=123123",
      },
      date: "Time and Date",
      socialMedia: "Social Media",
      risk: "high",
    },
  ];

  const attachLinkContent = (
    <div className="attach-link-content">
      <div className="attach-link-content-url">
        <p>Content URL</p>
        <div className="input-content">
          <input
            className={`${!isValid && isActive ? "invalid" : ""}`}
            ref={inputRef}
            onKeyDown={(e) => e.key === "Enter" && isValid && handlePaste()}
            value={inputValue}
            onChange={handleInputChange}
            placeholder="Please copy and paste the content URL"
          />
          {!isValid && isActive && (
            <p className="invalid-url">Please enter a valid tiktok url.</p>
          )}
        </div>
        <Button
          onClick={handlePasteLink}
          className="outline"
          text={
            <>
              <img src={ContentCopy} alt="Upload icon" />
              Paste
            </>
          }
        />
      </div>
      {isLoading && <DirectLinkLoading />}
      {isSubmitted && !isLoading && (
        <DirectAttachAnalysisTable
          isUpload
          columns={["Content", "Time and Date", "Social Media", "Risk"]}
          // data={popupTableData}
          data={uploadedData}
        />
      )}
      {isSubmitted && !isLoading && (
        <div className="attach-link-content-justification">
          <p>Justification</p>
          <p>
            {uploadedData[0].justification}
          </p>
          {/* <p>
            According to the video, there are strong indications that the
            content might be high likely a scam. This is suggested by the
            involvement of a person associated with OctaFX, a company already
            listed by Bank Negara Malaysia and Securities Commission Malaysia as
            an unauthorised entity. Additionally, the video promises high
            returns on investment for joining their group, a claim that appears
            suspiciously unrealistic. Furthermore, the lack of transparency is
            evident as the speaker fails to provide detailed information on the
            investment process, focusing solely on potential profits for users.
          </p> */}
        </div>
      )}
      {!isSubmitted && !isLoading && (
        <div className="attach-link-content-multiple">
          <img src={ContentCopy} alt="Copy icon" />
          <p>Paste URL to Generate Content Analysis</p>
        </div>
      )}
    </div>
  );

  const footerContent = (
    <>
      <div className="attach-link-footer">
        <Button className="outline" text="Cancel" onClick={handleCancel} />
        <Button
          onClick={handleReport}
          disable={isLoading || !isValid}
          text="Report Content"
        />
      </div>
    </>
  );

  const titleContent = (
    <div className="title-content d-flex align-items-center justify-content-between w-100">
      Direct Link Analysis
      <div>
        <img src={Minus} alt="Minimize menu icon" onClick={handleMinimize} />
        <CloseIcon onClick={handleCancel} fill="#80EED3" />

        {/* <img src={CloseIcon} alt='Close icon' onClick={handleCancel} /> */}
      </div>
    </div>
  );

  const riskLevels = ["Select Risk Level", "High", "Medium", "Low"];

  const handleFilterChange = (value, filterKey) => {
    const updatedValue = value.includes("Select") ? null : value;
    setFilters((prevFilters) => ({
      ...prevFilters,
      [filterKey]: { ...prevFilters[filterKey], value: updatedValue },
    }));
  };

  return (
    <div className="direct-link-analysis-wrapper">
      <div className="actions">
        <div className="input-content">
          <SearchIcon fill="#FFFFFF66" />
          <input placeholder="Select Case ID" />
        </div>
        <Select
          options={riskLevels}
          defaultValue={"Select Risk Level"}
          placeholder={"Select Risk Level"}
          className="StatusDropdown"
          arrowSize={"15"}
          onChange={(value) => handleFilterChange(value, "global")}
        />
        {!isMinimized && (
          <Button
            onClick={handleOpenAttachLink}
            className="outline"
            text={
              <div className="d-flex align-items-center gap-3">
                <PlusIcon fill="#fff" />
                Add New Link Analysis
              </div>
            }
          />
        )}
        {isMinimized && <MinimizedProcess openDialog={handleOpenAttachLink} />}
      </div>
      {tableDataLoading && <div className="loader">
          <img src={LoaderGif} alt="Loader gif" />
        </div>}
        {tableDataError && <div className="empty-state">
          <p>Network error. Please try again</p></div>}
      {!isMinimized && uploadedData.length === 0 && !tableDataLoading && !tableDataError && (
        <div className="empty-state">
          <p>
            There is no Link Analysis available, create a new Link Analysis to
            start.
          </p>
          <Button
            onClick={handleOpenAttachLink}
            className="outline"
            text={
              <div className="d-flex align-items-center gap-3">
                <PlusIcon fill="#fff" />
                Add New Link Analysis
              </div>
            }
          />
        </div>
      )}
      <DirectAttachAnalysisTable
        openDialog={showContentDetails}
        isEmpty={uploadedData.length === 0}
        isSelectable
        columns={[
          "Case ID",
          "Time and Date",
          "Social Media",
          "Topic",
          "Status",
          "Risk",
        ]}
        data={uploadedData}
      />
      <CustomModal
        className="direct-link"
        isOpen={isAttachOpen}
        title={titleContent}
        content={attachLinkContent}
        subTitle="Create direct analysis from the social media content links you attach"
        footer={footerContent}
      />
      <Alert
        message="Content has been successfully reported"
        info="success"
        duration={3000}
        visible={showMessage}
      />
    </div>
  );
};

export default DirectLinkAnalysis;
