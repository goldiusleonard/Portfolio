import endpoints from '../config/config.dev'
import axios from 'axios';


const url = endpoints.login;
// const url='http://192.168.30.235:8080/login_authentication_router/token';

export function capitalizeFirstLetter(string) {
    if (typeof string !== 'string') {
      // throw new TypeError('Expected a string');
      return;
    }
    return string.charAt(0).toUpperCase() + string.slice(1);
  }



  export const getLoginDetails = async (data) => {
    const { email, password } = data;

    const config = {
      method: 'post', // Use provided method (default 'get')
      maxBodyLength: Infinity,
      url: `${url}?email=${email}&password=${password}`,
      headers: {
        'accept': 'application/json'
      }
    };
    try {
      const response = await axios.request(config);
      if (response?.status === 200) {
        saveUserToLocalStorage(response?.data)
        return {user:response?.data,error:null}
      }
     
    


    } catch (error) {
      console.log('error', error)
throw error?.response?.data?.detail?? error.message
    }
  };
  
  
  export const saveUserToLocalStorage = (userData) => {
    localStorage.setItem('user', JSON.stringify(userData));
  };
  
  export const getUserFromLocalStorage = () => {
    const storedUser = localStorage.getItem('user');
    return storedUser ? JSON.parse(storedUser) : null;
  };
  
  export const clearUserFromLocalStorage = () => {
    localStorage.removeItem('user');
  };

  