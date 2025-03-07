import React, { useEffect, useState } from "react";
import { Form, FormGroup, Label } from "reactstrap";
import data from "./data.json"; // Assuming your JSON data is stored in this file
import Select from "../Select/Select";

const ContentCategorySelection = (props) => {
  const { isAgentOutput, showEditableScreen, crawlingStartDate, crawlingEndDate } = props;
  const [category, setCategory] = useState(props.category ?? "");
  const [subCategory1, setSubCategory1] = useState(props.subcategory ?? "");
  const [subCategory2, setSubCategory2] = useState(props.topic ?? "");
  const isEditable = showEditableScreen;

  const handleCategoryChange = (e) => {
    setCategory(e);
    setSubCategory1("");
    setSubCategory2("");
  };

  const handleSubCategory1Change = (e) => {
    setSubCategory1(e);
    setSubCategory2("");
  };

  useEffect(() => {
    if (isAgentOutput) {
      setCategory("Scam");
      setSubCategory1("Cryptocurrency");
      setSubCategory2("Bitcoin");
    }
  }, [isAgentOutput]);

  const getBreadcrumb = () => {
    let breadcrumb = [];
    if (props.category)
      breadcrumb.push(
        <span key="category" className="breadcrumb-part">
          {props.category}
        </span>
      );
    if (props.subcategory)
      breadcrumb.push(
        <span key="subcategory" className="breadcrumb-part">
          {props.subcategory}
        </span>
      );
   
    return breadcrumb.map((part, index) => (
      <React.Fragment key={index}>
        {part}
        {index < breadcrumb.length - 1 && (
          <span style={{ opacity: 0.5 }}> / </span>
        )}
      </React.Fragment>
    ));
  };


  

  const CategorySelection = data.categories.map((cat) => cat.name);

  const SubCategorySelection = category
    ? data.categories
        .find((cat) => cat.name === category)
        ?.subCategories.map((sub) => sub.name) || []
    : [];

  const TopicSelection = subCategory1
    ? data.categories
        .find((cat) => cat.name === category)
        ?.subCategories.find((sub) => sub.name === subCategory1)?.topics || []
    : [];

  return (
    <>
      {!isEditable ? (
        <>
          <div className="agent-category-container">
            <div className="validity-wrapper">
              <div className="validity-title">
                <span>Crawling Period </span>
              </div>
              <div className="validity-text">
                <span>{crawlingStartDate} - {crawlingEndDate}</span>
              </div>
            </div>
            <div className=" category-breadcrumb-title mb-2 mt-2">
              Category & Subcategory
            </div>
            <div className="category-breadcrumb text-truncate">
              {getBreadcrumb()}
            </div>
          </div>
        </>
      ) : (
        <Form className="w-100 p-3 h-100" style={{ borderRadius: "8px" }}>
          <div
            className={`form-container ${!isAgentOutput ? "h-100" : "h-80"}`}
          >
            <FormGroup>
              <Label for="category" className="text-light">
                Content Category Selection
              </Label>
            </FormGroup>
            <FormGroup>
              {isAgentOutput ? (
                <div className="category-field">Scam</div>
              ) : (
                <Select
                  options={CategorySelection}
                  defaultValue={"Select Category"}
                  placeholder={"Select Category"}
                  className="category-select StatusDropdown"
                  arrowSize={"15"}
                  onChange={handleCategoryChange}
                />
              )}
            </FormGroup>
            <FormGroup>
              {isAgentOutput ? (
                <div className="category-field">Cryptocurrency</div>
              ) : (
                <Select
                  options={SubCategorySelection}
                  defaultValue={"Select Sub-Category"}
                  placeholder={"Select Sub-Category"}
                  className="category-select StatusDropdown"
                  arrowSize={"15"}
                  disabled={!category}
                  onChange={handleSubCategory1Change}
                />
              )}
            </FormGroup>
          </div>
        </Form>
      )}
    </>
  );
};

export default ContentCategorySelection;
