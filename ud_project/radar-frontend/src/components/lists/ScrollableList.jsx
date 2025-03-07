import React, { useEffect, useMemo } from 'react'
import './scrollableList.scss'
import List from './List'
import LoaderAnimation from '../LoaderAnimation'

function ScrollableList({highlightedContent, name, setDate, creatorScamsData, date, years,loading, currentYear }) {
  // const [selectedYear, setSelectedYear] = React.useState(years[0] ?? "")

  // const choosenYearData = useMemo(() => {
  //   return creatorScamsData[selectedYear]?.data??[]; 
  // }, [selectedYear, creatorScamsData])

  
  function getLast12MonthsData(data) {
    if(!data) return[];
    const result = [];
    const now = new Date();
    const twelveMonthsAgo = new Date(now.setMonth(now.getMonth() - 12));

    data?.years?.forEach(year => {
        if (data[year]) {
            data[year]?.data?.forEach(content => {
                const contentDate = new Date(content.date);

                if (contentDate >= twelveMonthsAgo) {
                    result.push(content);
                }
            });
        }
    });

    // Sort (most recent first)
    result.sort((a, b) => {
        const dateA = new Date(a.date);
        const dateB = new Date(b.date);
        return dateB - dateA;
    });

    return result;
}

  return (
    <div className='cont'>
      {/* <div className='cont-left'>
        {years.map((year, index) => {
            const btnClass = `cont-button ${selectedYear === year ? 'cont-button-active' : ''}`
          return(
            <button
              key={index}
              className={btnClass}
              onClick={() => {
                setSelectedYear(year);
                currentYear(year);
            }}
            >
              {year}
            </button>
          )}
        )}

      </div> */}
      <div className='cont-right'>
        {loading ? <LoaderAnimation /> : <List highlightedContent={highlightedContent} name={name}  data={creatorScamsData && getLast12MonthsData(creatorScamsData)} date={date} setDate={setDate} />}
      </div>

    </div>
  )
}

export default ScrollableList
