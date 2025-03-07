// AuthContext.js
import React, { createContext, useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import endpoints from '../config/config.dev'
import axios from 'axios';
import useApiData from '../hooks/useApiData'

const url = 'http://192.168.30.200:8080/login_authentication_router/token'

// 'http://192.168.30.234:8000/login_authentication_router/token?email=shakil.s%40userdata.tech&password=shakil%40123'

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const navigate = useNavigate();

  const getLoginDetails = async (data) => {
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
      if (response.status === 200) {
        return response.data
      }
    
      // console.log(response?.data); // Handle successful response


    } catch (error) {
      console.log(error?.response?.detail); // Handle error

    }
  };
  
  const saveUserToLocalStorage = (userData) => {
    localStorage.setItem('user', JSON.stringify(userData));
  };
  
  const getUserFromLocalStorage = () => {
    const storedUser = localStorage.getItem('user');
    return storedUser ? JSON.parse(storedUser) : null;
  };
  
  const clearUserFromLocalStorage = () => {
    localStorage.removeItem('user');
  };
  


  const login = async (loginData) => {
    const user = await getLoginDetails(loginData);
    console.log('user==', user)
    saveUserToLocalStorage(user)
    if (!user) return;
    // localStorage.setItem('isAuthenticated', true);
    // localStorage.setItem('userRole', user.role);
    // localStorage.setItem('access_token', user.access_token)


    // setIsAuthenticated(true);
    // setUserRole(user.role);


    if (user?.role && user?.role === 'Officer') {
      navigate('/category-details');
    } else if (user?.role === 'SeniorLeader') {
      navigate('/dashboard');
     
    }



  };

  const logout = () => {
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('userRole');
    // setIsAuthenticated(false);
    // setUserRole('');
    navigate('/login');
    clearUserFromLocalStorage()
  };

  return (
    <AuthContext.Provider value={{ login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
