import React, { useEffect, useMemo, useState } from "react";
import useBreadcrumb from "../../hooks/useBreadcrumb";
import { useLocation } from "react-router-dom";
import { Mindmap } from "../../components/mindmap/Mindmap";
import useApiData from "../../hooks/useApiData";
import endpoints from "../../config/config.dev";
import { SearchIcon, SwitchCatIcon } from "../../assets/icons";
import Button from "../../components/button/Button";
import CategorySelectionModal from "../../components/Modal/CategorySelectionModal";
import CategoryComparer from "../../components/CategoryComparer";
import CategoryDetailCard from "../../components/VisualCharts/CategoryDetailCard";
import justifcationStaticData from "../../data/sampleJson/Justification.json";
import CategoryInfoTabs from "../../components/CategoryInfoTabs";
import { getUserFromLocalStorage } from "../../Util";

const initialAlert = {
  show: '',
  type: '',
  message: ''
}

const initialSubCategory = {
  subCategory: "",
  topic: "",
}

const CategoryInsight = () => {
  const user = getUserFromLocalStorage()
  const token = user?.access_token
  const location = useLocation();
  const [currentCategory, setCurrentCategory] = useState([]);
  const { subCategoryRoute } = location.state || "";
  const [subCategory, setSubCategory] = useState(initialSubCategory);
  const [alert, setAlert] = useState(initialAlert);

  const [modalOpen, setModalOpen] = useState(false);
  const title = "Category Insight";
  const hasBackButton = false;
  const hasDateFilter = true;
  const hasCategoryFilter = true;

  useBreadcrumb({ title, hasBackButton, hasDateFilter, hasCategoryFilter });
  const { data: keywordTrendsData, loadingData: keywordTrendsLoading, refetch: keywordTrendsDataRefetch } = useApiData(
    `${endpoints.getKeywordTrends}?${currentCategory.map(v => `categories=${v}`).join('&')}`,
    'GET',
    { enabled: false }
  );
  const { data: categoriesData, loading: categoriesDataLoading } = useApiData(endpoints.category)
  const { data: searchCategoryData, loading: searchCategoryLoading, refetch: searchCategoryRefetch } = useApiData(
    `${endpoints.getSearchCategories}?${currentCategory.map(v => `categories=${v}`).join('&')}`
  )

  useEffect(() => {
    if (!categoriesDataLoading && categoriesData && categoriesData.categories.length > 1) {
      setCurrentCategory([categoriesData.categories[0].name])
    }
  }, [categoriesData, categoriesDataLoading])

  useEffect(() => {
    if (currentCategory.length) {
      keywordTrendsDataRefetch()
    }

    if (currentCategory.length > 1) {
      searchCategoryRefetch()
    }
  }, [currentCategory])

  const getJustificationTextMemo = useMemo(() => {
    if (currentCategory.length === 1) {
      return justifcationStaticData.justification[currentCategory[0]]
    }

    if (currentCategory.length === 2) {
      const selectedCategoryJoined = `${currentCategory[0]},${currentCategory[1]}`
      return justifcationStaticData.justification[selectedCategoryJoined]
    }

    return null
  }, [currentCategory])

  const toggleModal = () => {
    setModalOpen(!modalOpen);
  };

  const handleUpdateCategories = (selectedCategory) => {
    setCurrentCategory(selectedCategory);
  };

  const getSubCategory = (key, value) => {
    // setCurrentCategory([value]);
    if (key === 'category') {
      setSubCategory(initialSubCategory)
      return
    }

    if (key === "subCategory" || key === "sub_category") {
      setSubCategory((prev) => ({ ...prev, topic: "" }));
      setSubCategory((prev) => ({ ...prev, subCategory: value }));
    }
    setSubCategory((prev) => ({ ...prev, [key]: value }));
  };

  const filteredCategories = currentCategory
    .map((category) =>
      categoriesData.categories.find((detail) => detail.name === category)
    )
    .filter(Boolean);

  return (
    <div className="category-page-wrapper insight">
      <section className="mindMap-wrapper">
        {currentCategory.length == 1 ? (
          <div className="d-flex justify-content-between search-wrapper align-items-center">
            <div className="search-input">
              <SearchIcon fill="#FFFFFF40" />
              <input
                type="text"
                placeholder="Search Category, Sub-Category, or Topic"
              />
            </div>
            <Button
              text={
                <>
                  <span className="icon">
                    <SwitchCatIcon fill="#FFFFFF99" />
                  </span>
                  Category Comparison
                </>
              }
              variant="cat-switch-button"
              onClick={toggleModal}
            />
          </div>
        ) : (
          <CategoryComparer
            currentCategory={currentCategory}
            toggleModal={toggleModal}
            handleUpdateCategories={handleUpdateCategories}
          />
        )}

        {currentCategory && currentCategory.length == 1 ? (
          <div className="minMap-chart card-wrap">
            <Mindmap
              label={subCategory.subCategory}
              setCategory={getSubCategory}
              topic={subCategory.topic}
              currentCategory={currentCategory[0]}
            />
          </div>
        ) : (
          <div className="category-detail-cards-wrapper">
            {searchCategoryData && searchCategoryData?.categories?.map((detail, idx) => (
              <div>
                <CategoryDetailCard
                  key={idx}
                  category={detail.name}
                  totalSubCategory={detail.totalSubCategory}
                  totalTopics={detail.totalTopics}
                  aboutCategory={detail.about}
                  sentiment={detail.sentiment}
                  risk={detail.risk}
                />
              </div>
            ))}
          </div>
        )}
      </section>
      <section className="category-cards-wrapper">
        <CategoryInfoTabs
          categories={filteredCategories.map(v => v.name)}
          subCategory={subCategory}
          currentCategory={currentCategory}
          categoryDetails={searchCategoryData ? searchCategoryData?.categories : []}
          words={keywordTrendsData ? keywordTrendsData?.keywordTrends : []}
          totalReportedCases={searchCategoryData ? searchCategoryData?.totalReportedCases : ''}
          justification={getJustificationTextMemo}
        />
      </section>
      <CategorySelectionModal
        isOpen={modalOpen}
        toggle={toggleModal}
        categoriesData={categoriesData && categoriesData.categories.length ? categoriesData : []}
        currentCategory={currentCategory}
        handleUpdateCategories={handleUpdateCategories}
      />
    </div>
  );
};

export default CategoryInsight;
