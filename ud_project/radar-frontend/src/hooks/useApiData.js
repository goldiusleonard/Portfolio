// import { useQuery } from 'react-query';
// import axios from 'axios';

// function useApiData(apiUrl) {
//   const token = localStorage.getItem('token')
//   const fetchApiData = async () => {
//     const response = await axios.get(apiUrl);
//     return response.data;
//   };

//   const { data, isLoading: loadingData, error } = useQuery(apiUrl, fetchApiData);

//   return { data, loadingData, error };
// }

// export default useApiData;


import { useQuery } from 'react-query';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { getUserFromLocalStorage } from '../Util';

const useApiData = (url, method = 'get', queryOptions = {}) => {
  const navigate = useNavigate();
  const user = getUserFromLocalStorage()
  const token = user?.access_token
// console.log("token",token);

  const fetchApiData = async () => {

    const config = {
      method,
      maxBodyLength: Infinity,
      url,
      headers: {
        accept: 'application/json',
        Authorization: `Bearer ${token}`,
      },

    };
    const res = await axios.request(config)
    return res.data
  }

  const { data, isLoading: loadingData, error, refetch } = useQuery(url, fetchApiData, {
    enabled: !!token,
    onError: (error) => {
      if (error.response && error.response.status === 401) {
        // Handle invalid token (e.g., logout, redirect to login)

        // localStorage.setItem("isAuthenticated",false);
        navigate('/login')

        // Implement your logout or redirection logic here
      } else if (error.response && error.response.status === 422) {
        console.log(error)
        return;
      } else {
        // Handle other errors
        console.error('API error:', error);
      }
    },
    ...queryOptions
  });



  return { data, loadingData, error, refetch };
}

export default useApiData;