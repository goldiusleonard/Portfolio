import React, { useEffect, useState } from "react";
import CustomModal from "../custom-modal/CustomModal";
import Button from "../button/Button";
import { SwitchCatIcon } from "../../assets/icons";
import Select from "../Select/Select";
// import categoriesData from "../../data/sampleJson/CatSubCatData.json";

const CategorySelectionModal = ({
  isOpen,
  toggle,
  categoriesData,
  currentCategory,
  handleUpdateCategories,
}) => {
  const [selectedCategory, setSelectedCategory] = useState('');

  useEffect(() => {
    if (categoriesData && categoriesData.categories?.length > 1) {
      setSelectedCategory(categoriesData?.categories[0].name)
    }
  }, [categoriesData])

  const selectedCategoryData = categoriesData?.categories?.find(
    (category) => category.name === selectedCategory
  );

  const subcategoriesCount = selectedCategoryData?.subCategories.length || 0;
  const topicsCount =
    selectedCategoryData?.subCategories.reduce(
      (total, sub) => total + (sub.topics?.length || 0),
      0
    ) || 0;

  const about = selectedCategoryData?.about || "No description available";

  const handleAddCategory = () => {
    if (currentCategory.includes(selectedCategory)) {
      toggle();
      return;
    }
    handleUpdateCategories([...currentCategory, selectedCategory]);
    toggle();
  };

  useEffect(() => {
    if (categoriesData.length) {
      setSelectedCategory(categoriesData?.categories[0].name);
    }
  }, [currentCategory]);

  return (
    <CustomModal
      isOpen={isOpen}
      toggle={toggle}
      size={"lg"}
      title="Category Comparison"
      subTitle="Create direct analysis from the social media content links you attach"
      content={
        <div className="modal-content-body">
          <div className="form-group">
            <label>Category</label>
            <div className="category-selection">
              {currentCategory &&
                currentCategory?.map((item, index) => (
                  <div key={item + index}>
                    <span>{item}</span>
                    {index !== currentCategory.length - 1 && (
                      <span className="icon">
                        <SwitchCatIcon fill="#FFFFFF" />
                      </span>
                    )}
                  </div>
                ))}

              <Select
                options={categoriesData?.categories?.map(
                  (category) => category.name
                ) || []}
                defaultValue={categoriesData && categoriesData?.categorie?.length ? categoriesData.categories[0]?.name : ''}
                onChange={(e) => setSelectedCategory(e)}
                className="categoryDropdown"
                arrowSize={"15"}
              />
            </div>
          </div>
          <ul className="category-description">
            <li>{`${selectedCategory} Category has ${subcategoriesCount} Sub-Categories and ${topicsCount} Topics`}</li>
            <li>{about}</li>
          </ul>
        </div>
      }
      footer={
        <div className="modal-footer-buttons mt-5">
          <Button text="Cancel" className="cancel-button" onClick={toggle} />
          <Button
            text="Submit"
            className="submit-button"
            onClick={handleAddCategory}
          />
        </div>
      }
    />
  );
};

export default CategorySelectionModal;
