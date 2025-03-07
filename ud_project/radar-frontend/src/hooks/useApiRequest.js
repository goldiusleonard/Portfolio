import axios from "axios";
import { getUserFromLocalStorage } from "../Util";
import { useNavigate } from "react-router-dom";
import { QueryClient } from "react-query";

export const queryClient = new QueryClient();

export function useApiRequest() {
  const navigate = useNavigate(); 
 

  async function apiRequest(method, url, data = null, customHeaders = {}) {
    const user = getUserFromLocalStorage();
    const token = user?.access_token;

    const headers = {
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
      ...customHeaders,
    };

    return axios({
      method,
      url,
      data,
      headers,
    })
      .then((response) => response.data)
      .catch((error) => {
        if (error.response) {
          // Handle authentication error (401) by navigating to login
          if (error.response.status === 401) {
            navigate("/login");
          }

          // Handle validation error (422) by logging the error
          if (error.response.status === 422) {
            console.error("Validation Error:", error.response.data);
          }
        }

        // Always reject the promise so React Query can handle it
        return Promise.reject(error);
      });
  }

  return { apiRequest };
}
