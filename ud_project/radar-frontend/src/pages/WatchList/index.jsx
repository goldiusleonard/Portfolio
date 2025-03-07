import React, { useRef,useState,useEffect } from 'react'
import LeaderBoard from '../../components/charts/BarChart'
import TableWithSearchbar from '../../components/tables/TableWithSearchbar';
import { scammersRankingHeadersWatchList } from '../../data/scammerRank';
import useBreadcrumb from '../../hooks/useBreadcrumb';
import useApiData from '../../hooks/useApiData';
import endpoints from '../../config/config.dev';
import LoaderAnimation from '../../components/LoaderAnimation';
import WatchListRanking from '../../components/WatchlistRanking';
import WatchlistRankingList from '../../components/lists/WatchlistRankingList';
import { useNavigate } from 'react-router-dom';

const WatchList = () => {
    const navigate = useNavigate();
  const [creatorProfiles, setCreatorProfiles] = useState([]);
  const [sortedData, setSortedData] = useState([]);
  const { data, loadingData } = useApiData(endpoints.getCreatorRanking);
  const title = 'Watchlist'; 
	const hasBackButton = false;
  const hasDateFilter = true;
  const hasCategoryFilter = true;

  useBreadcrumb({ title, hasBackButton, hasDateFilter, hasCategoryFilter });

  const ref = useRef(null);

  const scrollHeight = ref.current?.offsetHeight - 84;

  

  const fetchCreatorProfile = async (apiEndpoint) => {
    const response = await fetch(apiEndpoint);
    const data = await response.json();
    return data;
  };

  useEffect(() => {
    if (data && data.length > 0) {
      const sorted = data.sort((a, b) => a.rank - b.rank).slice(0, 3);
      setSortedData(sorted);
    }
  }, [data]);


  useEffect(() => {
    
    if (sortedData.length === 0) {
      return;
    }

    const fetchCreatorProfiles = async () => {
      try {
        const apiCalls = sortedData.map((user) => {
          const apiEndpoint = `${endpoints.getCreatorProfile}?userName=${user.user_handle}`;
          return fetchCreatorProfile(apiEndpoint);
        });

        const results = await Promise.all(apiCalls);

        const profileDataArray = results.map((result, index) => ({
          profileData: result
        }));

        setCreatorProfiles(profileDataArray);
      } catch (error) {
        console.error('Error fetching creator profiles:', error);
      }
    };

    fetchCreatorProfiles();
  }, [sortedData, endpoints]);

    const onClickRankListRow = (row) => {

    navigate('/watch-list/creator', { state: row.data }); // all row.data is passed for now we might need to pass only the id or userName 
  };


  const tableProps = {
    tableProps: {
      headers: scammersRankingHeadersWatchList,
      scrollHeight: scrollHeight,
    },
    searchProps: {
      placeholder: 'Search Creator',
     
    },
    data: data?.slice(3),
    loadingData,
    onRowClick:onClickRankListRow
  }

  return (
    <div className='watch-list-wrapper'>
      <section className='bar-chart-wrapper card-wrap'>
        { loadingData ? <LoaderAnimation /> : <>
          <WatchListRanking topRankers={creatorProfiles} />
          <WatchlistRankingList /> 
        </>  
        } 
      </section>
      <section className='rank-list-wrapper card-wrap' ref={ref}>
        <TableWithSearchbar {...tableProps} />
      </section>
    </div>
  )
}

export default WatchList
