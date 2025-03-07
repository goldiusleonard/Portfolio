import React, { useState } from 'react';
import ReactApexChart from 'react-apexcharts';
import LoaderAnimation from '../../LoaderAnimation';
import { capitalizeFirstLetter } from '../../../Util';
import useApiData from '../../../hooks/useApiData'
import endpoints from '../../../config/config.dev';




export const Treemap = ({  setSubCategory, handleStatusCardClick, activeTopic ,treeRef,subCategory}) => {
const [ subcatSelected,setSubcatSelected]=useState(!!subCategory?.subCategory)
  const { data, loadingData ,error} = useApiData(`${endpoints.getContentFilter}`);
  const treemapHeight = treeRef.current?.offsetHeight -(subcatSelected? 60:0)
  const [subCat, setSubCat] = useState(subCategory?.subCategory??'subCategory');
  const [navTitle, setNavTitle] = useState({
    subcat: subCategory.subCategory,
    topic: subCategory.topic,
  })
  
  const fomattedData = React.useMemo(()=>{
    
    return transformData(data,subCat)

  },[data, subCat])

  if(!data||error) return;




  const handleItemPressed = (key, value) => {
    if(key==='subcat'){
      setNavTitle(pre => ({ ...pre, topic: ''}))
    }
    setNavTitle(pre => ({ ...pre, [key]: value }))

  }

  const handleGoBack = () => {
    handleStatusCardClick(subCat, true)
    setNavTitle({
      topic: '',
      subcat: ''
    })

    setSubCategory({
      subCategory: '',
      topic: ''
    })
     setSubCat('subCategory')
    setSubcatSelected(false)
  };

  const chartData = {
    series: [
      {
        data:fomattedData??[]
      },
    ],
    options: {
      legend: {
        show: true,
      },

      colors: ['#0D1117'],
      stroke: {
        colors: ['#353535'],
        width: 0.3,


      },
      tooltip: {
        enabled: false,
      },



      dataLabels: {

        style: {
          colors: ['#A9A9A9'],
          fontSize: '14px',
          fontFamily: 'Helvetica, Arial, sans-serif',
          fontWeight: 'bold',
          
        },
        formatter: function (text, op) {
          return [capitalizeFirstLetter(text), op.value.toFixed(1) + "%"];
        },
   
      },
      plotOptions: {
        treemap: {
          enableShades: false,
          shadeIntensity: 1,

        }
      },
      chart: {
        type: 'treemap',
        toolbar: {
          show: false
        },

        events: {
          dataPointSelection: function (e, chart, options) {
            const label = options.w.globals.categoryLabels[options.dataPointIndex]
         
            if (subcatSelected) {
              // setTopic(label)
              handleItemPressed('topic', label)
              // handleStatusCardClick(label, false, 'topic')
          
              setSubCategory(pre => ({ ...pre, topic: label }))

            } else {
              setSubCat(label)
              setSubCategory(label)
              //  handleStatusCardClick(label, false, 'sub')
              handleItemPressed('subcat', label)
              setSubCategory(pre => ({ ...pre, subCategory: label }))
            }
            // handleStatusCardClick(label)

            setSubcatSelected(true)




          },
        },
      },
      title: {
        text: ""
      },
    },
  };
const handleSubCategoryTitleClick = ()=>{
  handleStatusCardClick(navTitle.subcat, false, 'sub')
  setNavTitle(prev=>({...prev,topic:''}))
}
  return <>
 { loadingData? 
  <LoaderAnimation />
 :  <>
     
        {subcatSelected &&
        <div className="filter-nav">
            <nav aria-label="breadcrumb">
              <ol className="breadcrumb">
                <li
                  className='breadcrumb-item'
                  onClick={handleGoBack}
                >
                  <span> Hate Speech </span>

                </li>
                <li
                  className={`breadcrumb-item ${!activeTopic && 'active'}`}
                  onClick={handleSubCategoryTitleClick}
               
                >
                  <span>{navTitle.subcat}</span>

                </li>
                {navTitle.topic &&
                  <li
                    className={`breadcrumb-item ${navTitle.topic && 'active'}`}
                   
                  >
                    <span>{navTitle.topic}</span>
                  </li>
                }
              </ol>
            </nav>
          </div>
        }
    
      
        <div className='treemap-chart'>
        <ReactApexChart options={chartData.options} series={chartData.series} type="treemap" height={treemapHeight}  loading={loadingData}/>
        </div>
      
    </>}
    </>
  
};

function transformData(data, topic) {
  if (!data || !topic) return;
  const newData = {};

  if (!!data) {
    for (const key in data) {
      if (Array.isArray(data[key])) {
        newData[key] = data[key].map(item => ({ x: item.name, y: item.percentage }));
      } else if (typeof data[key] === 'object' && data[key] !== null && data[key].topics) {
        newData[key] = data[key].topics.map(topic => ({ x: topic.name, y: topic.percentage }));
      }
    }

    if (newData[topic]) {
      // Sort the data in descending order based on 'y' value (percentage)
      newData[topic].sort((a, b) => b.y - a.y);
      return newData[topic];
    } else {
      return newData['subCategory']
    }
  }else{
    return;
  }
}
