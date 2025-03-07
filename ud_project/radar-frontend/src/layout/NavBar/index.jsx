import React, { useState } from "react";
import NavItem from "./NavItem";
import UserCard from "./UserCard";
import {
	ArchiveIcon,
	AwardStarIcon,
	CategoryIcon,
	DashboardIcon,
	LogoutIcon,
	SettingsIcon,
	WorkspaceIcon,
	OfficerDbIcon,
	MaximizeMenuIcon,
	MinimizeMenuIcon,
	CategoryInsight,
	AiIcon,
	DirectLinkIcon,
	LawViolationIcon
} from "../../assets/icons";
import { useAuth } from "../../contexts/AuthContext";
import ActivityIcon from "../../assets/icons/ActivityIcon";
import { clearUserFromLocalStorage, getUserFromLocalStorage} from "../../Util";

const NavBar = ({ key }) => {
	// const { userRole, logout } = useAuth();
	const user=getUserFromLocalStorage()
	const isOfficer = user?.role?.toLowerCase() === 'officer';

	const mainNavItems = [
    { href: "/dashboard", icon: DashboardIcon, label: "Dashboard" },
    // { href: "/category", icon: CategoryIcon, label: "Category" },
    { href: "/category-details", icon: OfficerDbIcon, label: "ReportHub" },
    {
      href: "/direct-link-analysis",
      icon: CategoryIcon,
      label: "Direct Link Analysis",
    },
    {
      href: "/category-insight",
      icon: CategoryInsight,
      label: "Category insight",
    },
    // { href: "/activity", icon: ActivityIcon, label: "Activity" },
    { href: "/watch-list", icon: AwardStarIcon, label: "Watchlist" },
    { href: "/ai-agent", icon: AiIcon, label: "AI Agent" },
    { href: "/law-violation", icon: LawViolationIcon, label: "Law Violation" },
  ];
  const otherNavItems = isOfficer
    ? [
        { href: "/archive", icon: ArchiveIcon, label: "Archive" },
        { href: "/settings", icon: SettingsIcon, label: "Settings" },
      ]
    : [{ href: "/settings", icon: SettingsIcon, label: "Settings" }];
  const [isOpen, setIsOpen] = useState(true);

  const toggleNavbar = () => {
    setIsOpen(!isOpen);
  };

  const filteredMainNavItems = mainNavItems.filter((item) => {
    if (isOfficer) {
      return (
        item.label !== "Dashboard" &&
        item.label !== "Category" &&
        item.label !== "Activity"
      );
    } else {
      return (
        item.label !== "ReportHub" &&
        item.label !== "Watchlist" &&
        item.label !== "Archive" &&
        item.label !== "Direct Link Analysis"
      );
    }
  });

	return (
		<div className={`nav-bar-wrapper ${isOpen ? "open" : ""}`}>
			<nav className={`left-nav-bar`}>
				{
					<div className="navigation-menu">
						<UserCard isOpen={isOpen} isOfficer={isOfficer} name ={user?.user_name}/>
						<div className="menu" onClick={toggleNavbar}>
							{isOpen ? (
								(
									<MinimizeMenuIcon fill={"#FFFFFF99"} />
								)
							) : <>
								<MaximizeMenuIcon fill={"#FFFFFF99"} />
								<span className="menu-text">Minimize Sidebar</span>
							</>
							}
						</div>
						<p>Main</p>
						{filteredMainNavItems.map((item, index) => {
							return (
								<NavItem
									label={item.label}
									isOpen={isOpen}
									Icon={item.icon}
									to={item.href}
									key={index}
								/>
							);
						})}
						<p>Other</p>
						{otherNavItems.map((item, index) => {
							return (
								<NavItem
									label={item.label}
									isOpen={isOpen}
									Icon={item.icon}
									to={item.href}
									key={index}
								/>
							);
						})}
					</div>
				}
				<button className="navigation-menu logout" onClick={clearUserFromLocalStorage}>
					<NavItem
						label={"Log Out"}
						isOpen={isOpen}
						Icon={LogoutIcon}
						to="/"
					/>
				</button>
			</nav>
		</div>
	);
};

export default NavBar;
