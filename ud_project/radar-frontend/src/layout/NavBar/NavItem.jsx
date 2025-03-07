import React, { useState } from "react";
import "./NavItem.scss";
import { NavLink } from "react-router-dom";

const NavItem = ({ Icon, label, active, isOpen, to ,color}) => {
	return (
		<NavLink to={to} className="nav-item">
		 {({ isActive }) => (
        <>
          <Icon fill={(!isActive) ? '#FFFFFF99' : '#000'} />
          {!isOpen && <span style={{color}}>{label}</span>}
        </>
      )}
		</NavLink>
	);
};

export default NavItem;
