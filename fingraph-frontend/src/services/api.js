const API_BASE_URL = "/api";

const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;

  console.log("🔥 API REQUEST:", url);

  try {
    const response = await fetch(url, {
      method: options.method || "GET",

      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },

      ...options,
    });

    console.log("🔥 API STATUS:", response.status);

    if (!response.ok) {
      let errorMessage = `Backend request failed: ${response.status}`;

      try {
        const errorData = await response.json();

        if (errorData?.detail) {
          errorMessage = errorData.detail;
        } else if (errorData?.message) {
          errorMessage = errorData.message;
        }
      } catch {
        // Ignore JSON parsing error
      }

      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (error) {
    console.error("❌ API ERROR:", error);
    throw error;
  }
};

// ======================================================
// FRAUD NETWORK
// ======================================================

export const getFraudNetwork = async (limit = 20) => {
  return apiRequest(
    `/fraud-network?limit=${encodeURIComponent(limit)}`
  );
};

// ======================================================
// OTHER APIs
// ======================================================

export const getStats = async () => {
  return apiRequest("/stats");
};

export const getTransactions = async () => {
  return apiRequest("/transactions");
};

export const getFraudAnalytics = async () => {
  return apiRequest("/fraud-analytics");
};

export const getFraudBreakdown = async () => {
  return apiRequest("/fraud-breakdown");
};

export const getRiskDistribution = async () => {
  return apiRequest("/risk-distribution");
};

export default apiRequest;