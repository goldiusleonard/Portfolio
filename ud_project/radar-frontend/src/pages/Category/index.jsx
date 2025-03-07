import React from 'react'
import { Mindmap } from '../../components';
import News from "../../components/CategoryNews/News";
import { useNavigate, useLocation } from 'react-router-dom';
import CategoryStatusCards from '../../components/CategoryStatusCard';
import useBreadcrumb from '../../hooks/useBreadcrumb';

const CategoryScreen = () => {
  const navigation =useNavigate();
  const location = useLocation();
  const { subCategoryRoute } = location.state || ''
  const [subCategory, setSubCategory]=React.useState({
   subCategory:subCategoryRoute,
   topic:''
  
  })
  
  const title = 'Category'; 
  const hasBackButton = false;
  const hasDateFilter = true; 

	useBreadcrumb({ title, hasBackButton, hasDateFilter });

  const handleViewDetail = () => {
    navigation('/category/category-details', { state:  subCategory });
  }

  const getSubCategory = (key,value) => {
    // reset the topic to default value
 
    if(key === 'subCategory'|| key ==='sub_category') {
      setSubCategory(prev=>({...prev,topic:''}))
      setSubCategory(prev=>({...prev,subCategory:value}))
    } 
    setSubCategory(prev=>({...prev,[key]:value}))
  }
  return (
    <div className="category-page-wrapper">
      <section className="mindMap-wrapper">
        {/* <div className="top-search-bar card-wrap"></div> */}
        <div className="minMap-chart card-wrap">
          <Mindmap
            label={subCategory.subCategory}
            setCategory={getSubCategory}
            topic={subCategory.topic}
          />
        </div>
      </section>
      <section className="category-cards-wrapper">
        <div className="category-cards card-wrap">
          <CategoryStatusCards
            subCategoryRoute={subCategory.subCategory}
            subCategoryTopic={subCategory.topic}
          />
        </div>
        <div className="category-news card-wrap">
          <News
            subCategory={subCategory.subCategory}
            subCategoryTopic={subCategory.topic}
          />
        </div>
        {/* <div className="btn-wrapper">
              <button className="btn-view-detail border-button" onClick={handleViewDetail}>View Detail</button>
          </div> */}
      </section>
    </div>
  );
}

export default CategoryScreen
