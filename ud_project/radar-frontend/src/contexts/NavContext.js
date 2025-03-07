import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';

const NavContext = createContext();

const defaultNavData = {
  hasBackButton: false,
  navItems: [],
  title: '',
  hasDateFilter: false,
  hasCategoryFilter: false,
};

export const NavProvider = ({ children }) => {
  const [navData, setNavData] = useState(defaultNavData);
  const location = useLocation();

  const updateNavData = useCallback((newData) => {
    setNavData((prevNavData) => ({ ...prevNavData, ...newData }));
  }, []);

  const resetNavData = useCallback(() => {
    setNavData(defaultNavData);
  }, []);

  const generateNavItemsFromUrl = (url) => {
    const paths = url.split('/').filter(path => path);
    const navItems = paths.map((path, index) => {
      const url = '/' + paths.slice(0, index + 1).join('/');
      return {
        url: url,
        name: path.replace(/-/g, ' ').replace(/^\w/, c => c.toUpperCase()),
        active: index === paths.length - 1,
      };
    });
    return navItems;
  };

  useEffect(() => {
    const newNavItems = generateNavItemsFromUrl(location.pathname);
    setNavData((prevNavData) => ({
      ...prevNavData,
      navItems: newNavItems,
      hasBackButton: newNavItems.length > 1,
    }));
  }, [location.pathname]);

  return (
    <NavContext.Provider value={{ navData, updateNavData, resetNavData }}>
      {children}
    </NavContext.Provider>
  );
};

export const useNav = () => useContext(NavContext);
