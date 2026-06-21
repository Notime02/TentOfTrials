import axios, { AxiosError, AxiosRequestConfig } from 'axios';

const apiClient = axios.create({
  baseURL: 'https://api.example.com',
  timeout: 1000,
});

// Function to refresh the token
async function refreshToken(): Promise<string | null> {
  try {
    const response = await axios.post('/auth/refresh', {
      // Include necessary data for token refresh
    });
    const newToken = response.data.token;
    // Store the new token in local storage or state management
    localStorage.setItem('authToken', newToken);
    return newToken;
  } catch (error) {
    console.error('Token refresh failed:', error);
    return null;
  }
}

// Interceptor to handle 401 responses
apiClient.interceptors.response.use(
  response => response,
  async (error: AxiosError) => {
    const originalRequest: AxiosRequestConfig = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const newToken = await refreshToken();
      if (newToken) {
        // Update the authorization header with the new token
        originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } else {
        // Clear stale auth state or handle error
        localStorage.removeItem('authToken');
        return Promise.reject(new Error('Token refresh failed. Please log in again.'));
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;