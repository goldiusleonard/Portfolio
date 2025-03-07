import React, { useState, createContext, useContext} from "react";
import { BrowserRouter as Router } from "react-router-dom";
import AppRoutes from "./routes";
import { NavProvider } from "./contexts/NavContext";
import { AuthProvider } from "./contexts/AuthContext";
import {StatusContextProvider } from "./contexts/StatusContext";


const GlobalStateContext = createContext()

function App() {
  const [creatorUsername, setCreatorUsername] = useState("Finihazlitc")
  const [analyticsData, setAnalyticsData] = useState({})
  const [subCategory, setSubCategory] = useState()
  const [AIAgentID, setAIAgentID] = useState(null);
  
  const [updatedAgentData, setUpdatedAgentData] = useState({});

  const globalValues = {
    creatorUsername, 
    setCreatorUsername,
    analyticsData,
    setAnalyticsData,
    subCategory, 
    setSubCategory,
    AIAgentID,
    setAIAgentID,
    updatedAgentData,
    setUpdatedAgentData
  }

  return (
    <GlobalStateContext.Provider value={globalValues}>
      <Router>
        <AuthProvider>
        <NavProvider>
          <StatusContextProvider>
          <AppRoutes />
          </StatusContextProvider>
          </NavProvider>
          </AuthProvider>
      </Router>
    </GlobalStateContext.Provider>
  );
}

export const useGlobalData = () => {
  return useContext(GlobalStateContext)
}

export default App;
