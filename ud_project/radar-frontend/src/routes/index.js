import React from "react";
import { Route, Routes, Navigate, Outlet } from "react-router-dom";
import AppLayout from "../layout/AppLayout";
import LandingPage from "../pages/LandingPage";
import Dashboard from "../pages/Dashboard";
import OverallContent from "../pages/OverallContent";
import ContentDetails from "../pages/ContentDetails";
import CreatorScreen from "../pages/CreatorScreen";
import WatchList from "../pages/WatchList";
import CategoryScreen from "../pages/Category";
import CategoryDetails from "../pages/CategoryDetails";
import Workspace from "../pages/Workspace";
import Archive from "../pages/Archive";
import LoginPage from "../pages/Login";
import ActivityPage from "../pages/ActivityPage";
import AddAgentBuilder from "../pages/AddAgentBuilder";
import AgentBuilder from "../pages/AgentBuilder";
import AgentContentDetails from "../pages/AgentContentDetails";
import CategoryInsight from "../pages/CategoryInsight";
import AgentBuilderDetails from "../pages/AgentBuilderDetails";
import NotAuthorized from "../pages/NotAuthorized";
import { getUserFromLocalStorage } from "../Util/index";
import Contents from "../components/Contents";
import CommentDetails from "../pages/CommentDetails";
import DirectLinkAnalysis from "../pages/DirectLinkAnalysis";
import LawViolation from "../pages/LawViolation";
import PDFContentDetails from "../pages/PDF/PDFContentDetails";
import PDFLaws from "../pages/PDF/PDFLaws";
import PDFCommentDetails from "../pages/PDF/PDFCommentDetails";
import PDFAccountDetail from "../pages/PDF/PDFAccountDetail";

const routes = [
  { path: "/dashboard", element: <Dashboard />, roles: ["SeniorLeader"] },
  {
    path: "/overall-content",
    element: <OverallContent />,
    roles: ["Officer"],
  },
  { path: "/watch-list", element: <WatchList />, roles: ["Officer"] },
  {
    path: "/watch-list/creator",
    element: <CreatorScreen />,
    roles: ["Officer"],
  },
  { path: "/category", element: <CategoryScreen />, roles: ["SeniorLeader"] },
  {
    path: "/category-details",
    element: <CategoryDetails />,
    roles: ["Officer"],
  },
  {
    path: "/category-details/content-details",
    element: <ContentDetails />,
    roles: ["Officer"],
  },
  {
    path: "/category-details/comment-details",
    element: <CommentDetails />,
    roles: ["Officer"],
  },
  { path: "/workspace", element: <Workspace />, roles: ["SeniorLeader"] },
  { path: "/activity", element: <ActivityPage />, roles: ["SeniorLeader"] },
  { path: "/archive", element: <Archive />, roles: ["Officer"] },
  {
    path: "/ai-agent",
    element: <AgentBuilder />,
    roles: ["SeniorLeader", "Officer"],
  },
  {
    path: "/ai-agent/agent-details/:agentID",
    element: <AgentBuilderDetails />,
    roles: ["SeniorLeader", "Officer"],
  },
  {
    path: "/ai-agent/agent-details/agent-content-details",
    element: <AgentContentDetails />,
    roles: ["SeniorLeader", "Officer"],
  },
  {
    path: "/category-insight",
    element: <CategoryInsight />,
    roles: ["Officer", "SeniorLeader"],
  },
  {
    path: "/ai-agent/add-agent",
    element: <AddAgentBuilder />,
    roles: ["SeniorLeader"],
  },
  // { path: "/settings", element: <LandingPage />, role: "Officer" },
  {
    path: "/ai-agent/agent-details/all-contents",
    element: <Contents />,
    roles: ["SeniorLeader", "Officer"],
  },

  {
    path: "/direct-link-analysis",
    element: <DirectLinkAnalysis />,
    roles: ["Officer"],
  },
  {
    path: "/law-violation",
    element: <LawViolation />,
    roles: ["SeniorLeader", "Officer"],
  },
  {
    path: "/pdf-content-details",
    element: <PDFContentDetails />,
    roles: ["Officer"],
  },
  {
    path: "/pdf-laws",
    element: <PDFLaws />,
    roles: ["SeniorLeader", "Officer"],
  },
  {
    path: "/pdf-comment-details",
    element: <PDFCommentDetails />,
    roles: ["Officer"],
  },
  {
    path: "/pdf-account-details",
    element: <PDFAccountDetail />,
    roles: ["Officer"],
  },

  { path: "*", element: <NotAuthorized /> },
  // Catch-all route for unmatched paths
];

const ProtectedRoute = ({ element, roles }) => {
  const user = getUserFromLocalStorage();
  if (!user?.access_token) {
    return <Navigate to="/login" />;
  }
  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/not-authorized" />;
  }
  return element;
};

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<AppLayout />}>
        {routes.map((route) => (
          <Route
            key={route.path}
            path={route.path}
            element={
              <ProtectedRoute {...route}>{route.element}</ProtectedRoute>
            }
          />
        ))}
        <Route path="/settings" element={<LandingPage />} />
      </Route>
    </Routes>
  );
}

export default AppRoutes;
