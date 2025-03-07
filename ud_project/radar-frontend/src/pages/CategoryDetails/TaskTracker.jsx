import React, { useMemo } from 'react'
import useApiData from '../../hooks/useApiData'
import endpoints from '../../config/config.dev'
import LoaderAnimation from '../../components/LoaderAnimation';
import { useNavigate, useNavigation } from 'react-router-dom';


const TaskTracker = () => {
    // const apiUrl = useMemo(
    //     // () => `${endpoints.getTaskAndPercentage}?category=Scam&subCategory=Forex&topic=Forex%20Investment`, [] // When filter need to implement
    //     () => `${endpoints.getTaskAndPercentage}`, []
    // );

    const { data, loadingData } = useApiData(endpoints.getTaskAndPercentage);

    const navigation = useNavigate()

    const goToArchive = () => {
        navigation('/archive')
    }

    return (
        <>
        { loadingData ? <LoaderAnimation /> :
        <>
            <section className='sec-tasks-count card-wrap'>
                <div className="inner-card assign-tasks">
                    <p>Assigned Content</p>
                    <label htmlFor="Count">{data?.total_assigned_count}</label>
                </div>
                <div className="inner-card reported-tasks">
                    <p>Reported Content</p>
                    <label htmlFor="Count">{data?.total_report_count}</label>
                </div>
                <button className='btn btn-outline-light' onClick={goToArchive}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <g id="arrow-icon">
                            <path id="Vector 1" d="M8 3L16 12L8 21" stroke="white" />
                        </g>
                    </svg>
                </button>
            </section>
            <section className='risk-levels card-wrap'>
                <div className="high">
                    <span className='r-label'>High</span>
                    <span>{data?.high?.toFixed(1)}%</span>
                </div>
                <div className="medium">
                    <span className='r-label'>Medium</span>
                    <span>{data?.medium?.toFixed(1)}%</span>
                </div>
                <div className="low">
                    <span className='r-label'>Low</span>
                    <span>{data?.low?.toFixed(1)}%</span>
                </div>
            </section>

        </> }
        </>
    )
}

export default TaskTracker
