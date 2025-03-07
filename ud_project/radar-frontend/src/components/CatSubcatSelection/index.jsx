import React, { useEffect, useState } from "react";
import { Form, FormGroup, Label } from "reactstrap";
import data from "../../data/sampleJson/CatSubCatData.json"; // Assuming your JSON data is stored in this file
import Select from "../Select/Select";
import CustomSelect from "../CustomSelect/CustomSelect";
import { useGlobalData } from "../../App";

const CatSubcatSelection = (props) => {
  const { isAgentOutput, setEditedAgentData} = props;
  
const [category, setCategory] = useState(props.agentCategory ?? "");
  const [subCategory1, setSubCategory1] = useState(
    props.agentSubcategory ?? ""
  );


  const handleCategoryChange = (e) => {
    setCategory(e);
    setSubCategory1("");
    setEditedAgentData((prev) => ({ ...prev, category: e }));
  };

  const handleSubCategory1Change = (e) => {
    setSubCategory1(e);
    setEditedAgentData((prev) => ({ ...prev, subcategory: e }));
  };

  useEffect(() => {
    if (isAgentOutput) {
      setCategory("Scam");
      setSubCategory1("Cryptocurrency");
    }
  }, [isAgentOutput]);

  const CategorySelection = data.categories.map((cat) => cat.name);

  const SubCategorySelection = category
    ? data.categories
        .find((cat) => cat.name === category)
        ?.subCategories.map((sub) => sub.name) || []
    : [];

  return (
    <Form className="w-100 p-3 h-100" style={{ borderRadius: "8px" }}>
      <div className={`form-container ${!isAgentOutput ? "h-100" : "h-80"}`}>
        <FormGroup>
          <Label for="category" className="text-light">
            Content Category Selection
          </Label>
        </FormGroup>
        <FormGroup>
          <CustomSelect
            options={CategorySelection}
            defaultValue={props.agentCategory || "Select Category"}
            onChange={handleCategoryChange}
            placeholder={props.agentCategory || "Select Category"}
            addInputPlaceholder={"Add new category"}
            arrowSize={"15"}
            className="category-select StatusDropdown"
            disabled={false}
          />
        </FormGroup>
        <FormGroup>
          <CustomSelect
            options={SubCategorySelection}
            defaultValue={props.agentSubcategory || "Select Sub-Category"}
            onChange={handleSubCategory1Change}
            placeholder={props.agentSubcategory || "Select Sub-Category"}
            addInputPlaceholder={"Add new sub-category"}
            arrowSize={"15"}
            className="category-select StatusDropdown"
            disabled={false}
          />
        </FormGroup>
      </div>
    </Form>
  );
};

export default CatSubcatSelection;
