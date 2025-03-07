import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useNav } from '../contexts/NavContext';

const useBreadcrumb = ({ title, hasBackButton, hasDateFilter, hasCategoryFilter }) => {
  const location = useLocation();
  const { updateNavData } = useNav();
  const subCategory = location.state != null ? location.state : '';

  useEffect(() => {
    const pathnames = location.pathname.split('/').filter((x) => x);
    const navItems = pathnames.map((value, index) => {
      const url = `/${pathnames.slice(0, index + 1).join('/')}`;
      return {
        url,
        name: value.charAt(0).toUpperCase() + value.slice(1)?.replace(/-/g, ' '),
        active: index === pathnames.length - 1,
      };
    });

    if (location.pathname === '/category/category-details' && subCategory.subCategory) {
      const customNavItems = [
        {
          url: '/category',
          name: 'Category',
          active: false
        },
        {
          url: '/category/category-details',
          name: subCategory.subCategory,
          active: true
        }
      ];
      updateNavData({
        hasBackButton,
        navItems: customNavItems,
        title: '',
        hasDateFilter,
        hasCategoryFilter,
      });
    } else if (title) {
      updateNavData({
        hasBackButton,
        navItems: [],
        title,
        hasDateFilter,
        hasCategoryFilter,
      });
    } else {
      updateNavData({
        hasBackButton,
        navItems,
        title: '',
        hasDateFilter,
        hasCategoryFilter,
      });
    }
  }, [location, title, hasBackButton, hasDateFilter, hasCategoryFilter, updateNavData, subCategory.subCategory]);
};

export default useBreadcrumb;
