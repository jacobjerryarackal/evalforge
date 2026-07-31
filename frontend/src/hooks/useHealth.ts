import { useState } from "react";
import { apiService } from "../services/api";

export function useHealth(initialState = true) {
  const [backendConnected, setBackendConnected] = useState(initialState);

  const checkHealth = async () => {
    const isOk = await apiService.checkHealth();
    setBackendConnected(isOk);
    return isOk;
  };

  return {
    backendConnected,
    setBackendConnected,
    checkHealth,
  };
}
