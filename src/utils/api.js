// API Base URL configuration
const DEV_API_URL = 'http://127.0.0.1:9027';
const PROD_API_URL = 'https://aceplus.vercel.app';

// For debugging
console.log('Current NODE_ENV:', process.env.NODE_ENV);
console.log('Current REACT_APP_ENV:', process.env.REACT_APP_ENV);

export const API_BASE_URL = process.env.NODE_ENV === 'production' ? PROD_API_URL : DEV_API_URL;

// Default headers that should be included in most requests
const getDefaultHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Authorization': token ? `Bearer ${token}` : '',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  };
};

// Helper function to check if response is JSON
const isJsonResponse = (response) => {
  const contentType = response.headers.get('content-type');
  return contentType && contentType.includes('application/json');
};

// API request wrapper with error handling
export const apiRequest = async (endpoint, options = {}) => {
  try {
    // Ensure endpoint starts with /
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${API_BASE_URL}${normalizedEndpoint}`;
    
    // Special handling for FormData
    const isFormData = options.body instanceof FormData;
    
    const headers = {
      ...(isFormData ? {} : getDefaultHeaders()), // Don't set default headers for FormData
      ...options.headers
    };

    // Always add Authorization header if token exists
    const token = localStorage.getItem('token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Remove Content-Type for FormData
    if (isFormData) {
      delete headers['Content-Type'];
    }

    // Set default timeout to 30 seconds, but use 120 seconds for image operations
    const isImageOperation = endpoint.includes('generate_from_images') || endpoint.includes('upload_images');
    const timeout = isImageOperation ? 120000 : 30000;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    const config = {
      ...options,
      headers,
      mode: 'cors',
      credentials: 'include',
      signal: controller.signal
    };

    console.log('Making request to:', url);
    console.log('With config:', {
      ...config,
      headers: { ...config.headers }
    });

    const response = await fetch(url, config);
    clearTimeout(timeoutId);
    
    // Log response details for debugging
    console.log('Response status:', response.status);
    console.log('Response headers:', [...response.headers.entries()]);

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user_id');
        window.location.href = '/login';
        throw new Error('Unauthorized access');
      }
      
      // Try to get error message from response
      let errorMessage = `Request failed with status ${response.status}`;
      if (isJsonResponse(response)) {
        const errorData = await response.json().catch(() => null);
        if (errorData) {
          errorMessage = errorData.msg || errorData.message || errorMessage;
        }
      }
      throw new Error(errorMessage);
    }

    // Handle successful response based on content type
    if (isJsonResponse(response)) {
      return await response.json();
    }

    // For non-JSON responses, return the raw response
    return response;
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('Request timed out. Please try again.');
    }
    console.error('API Request failed:', error);
    throw error;
  }
};

// Common API endpoints
export const endpoints = {
  userStats: 'api/user_stats',
  leaderboard: 'api/leaderboard',
  updates: 'api/updates',
  login: 'api/login',
  createExam: 'api/create_exam',
  submitExam: (examId) => `api/submit_exam/${examId}`,
  getExam: (examId) => `api/exam/${examId}`,
  getLessons: (subject, isClass10) => `api/lessons?subject=${subject}${isClass10 ? '&class10=true' : ''}`,
  getTests: 'api/tests',
  generateTest: 'api/generate_test',
  createTest: 'api/create_test',
  getUserExams: 'api/user_exams',
  getOverviewStats: 'api/overview_stats',
  getSubjectStats: (subject) => `api/subject_stats/${subject}`,
  reportQuestion: 'api/report',
  uploadImages: 'api/upload_images',
  getUploadedImage: (filename) => `api/uploads/${filename}`
};

// API methods for common operations
export const api = {
  getUserStats: () => apiRequest(endpoints.userStats),
  getOverviewStats: () => apiRequest(endpoints.getOverviewStats),
  getLeaderboard: () => apiRequest(endpoints.leaderboard),
  getUpdates: () => apiRequest(endpoints.updates),
  login: (data) => apiRequest(endpoints.login, {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  createExam: (data) => apiRequest(endpoints.createExam, {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  submitExam: (examId, data) => apiRequest(endpoints.submitExam(examId), {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  getExam: (examId) => apiRequest(endpoints.getExam(examId)),
  getLessons: (subject, isClass10 = false) => apiRequest(endpoints.getLessons(subject, isClass10)),
  getTests: () => apiRequest(endpoints.getTests),
  generateTest: (data) => apiRequest(endpoints.generateTest, {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  createTest: (data) => apiRequest(endpoints.createTest, {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  getUserExams: () => apiRequest(endpoints.getUserExams),
  getSubjectStats: (subject) => apiRequest(endpoints.getSubjectStats(subject)),
  reportQuestion: (data) => apiRequest(endpoints.reportQuestion, {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  uploadImages: (formData) => apiRequest(endpoints.uploadImages, {
    method: 'POST',
    body: formData
  }),
  generateFromImages: async (filenames, {
    onProgress = () => {},
    onMessage = () => {},
  } = {}) => {
    try {
      // Start the job
      const startResponse = await apiRequest('api/generate_from_images', {
        method: 'POST',
        body: JSON.stringify({ filenames })
      });

      const jobId = startResponse.job_id;
      console.log('Job started with ID:', jobId);

      // Return a Promise that resolves when processing is complete
      return new Promise((resolve, reject) => {
        const pollJob = async () => {
          try {
            const status = await apiRequest(`api/check_job_status/${jobId}`, {
              method: 'GET'
            });
            
            if (status.status === 'processing') {
              if (status.total > 0) {
                onProgress({
                  completed: status.completed || 0,
                  total: status.total
                });
              }
              // Continue polling
              setTimeout(pollJob, 1000);
            } else if (status.status === 'completed') {
              if (status.questions && Array.isArray(status.questions)) {
                resolve(status.questions);
              } else {
                reject(new Error('No questions could be extracted from the images'));
              }
            } else if (status.status === 'failed') {
              reject(new Error(status.message || 'Failed to process images'));
            }
          } catch (error) {
            reject(error);
          }
        };

        // Start polling
        pollJob();
      });
    } catch (error) {
      console.error('Error in generateFromImages:', error);
      throw error;
    }
  },
  getUploadedImage: (filename) => apiRequest(endpoints.getUploadedImage(filename), {
    method: 'GET',
    headers: {
      'Accept': 'image/*'
    }
  }),
  checkJobStatus: (jobId) => apiRequest(`api/check_job_status/${jobId}`, {
    method: 'GET'
  })
};