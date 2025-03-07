import { createContext, useContext, useState } from "react";

const StatusContext = createContext();

export const StatusContextProvider = ({ children }) => {
const [isAgentActive, setIsAgentActive] = useState(true)



    return <StatusContext.Provider value={{isAgentActive, setIsAgentActive}}>{children}</StatusContext.Provider>;
};

export const useStatus = () => useContext(StatusContext);