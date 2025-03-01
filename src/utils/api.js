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
  generateHint: 'api/generate_hint',
  generateSolution: 'api/generate_solution',
  getExam: (examId) => `api/exam/${examId}`,
  getLessons: (subject, isClass10) => `api/lessons?subject=${subject}${isClass10 ? '&class10=true' : ''}`,
  getTests: 'api/tests',
  generateTest: 'api/generate_test',
  createTest: 'api/create_test',
  getUserExams: 'api/user_exams',
  getOverviewStats: 'api/user_stats',
  getSubjectStats: (subject) => `api/subject_stats/${subject}`,
  reportQuestion: 'api/report',
  uploadImages: 'api/upload_images',
  getUploadedImage: (filename) => `api/uploads/${filename}`
};

// API methods for common operations
export const api = {
  getUserStats: () => apiRequest(endpoints.userStats),
  getOverviewStats: () => apiRequest(endpoints.getOverviewStats),
  getLeaderboard: (page = 1, pageSize = 20) => apiRequest(`${endpoints.leaderboard}?page=${page}&page_size=${pageSize}`),
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
    generateHint: async (question, { onProgress = () => {} } = {}) => {
      const response = await apiRequest(endpoints.generateHint, {
        method: 'POST',
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
          throw new Error(`Failed to generate hint: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      try {
          while (true) {
              const { done, value } = await reader.read();
              if (done) {
                  break;
              }
              buffer += decoder.decode(value, { stream: true });

              // Process the buffer immediately
              onProgress(buffer);
              buffer = ''; // Clear the buffer after processing
          }
      } catch (error) {
          console.error('Error reading stream:', error);
          throw error;
      } finally {
          reader.releaseLock();
      }
    },
    generateSolution: async (examId, questionIndex, { onProgress = () => {} } = {}) => {
      const response = await apiRequest(endpoints.generateSolution, {
        method: 'POST',
        body: JSON.stringify({ examId, questionIndex }),
      });

      if (!response.ok) {
          throw new Error(`Failed to generate solution: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      try {
          while (true) {
              const { done, value } = await reader.read();
              if (done) {
                  break;
              }
              buffer += decoder.decode(value, { stream: true });

              // Process the buffer immediately
              onProgress(buffer);
              buffer = ''; // Clear the buffer after processing
          }
      } catch (error) {
          console.error('Error reading solution stream:', error);
          throw error;
      } finally {
          reader.releaseLock();
      }
    },
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
  uploadImages: (formData, onProgress = () => {}) => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const percentComplete = (event.loaded / event.total) * 100;
          onProgress(percentComplete);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed'));
      });

      xhr.open('POST', `${API_BASE_URL}/api/upload_images`);
      
      // Add headers from getDefaultHeaders()
      const headers = getDefaultHeaders();
      Object.entries(headers).forEach(([key, value]) => {
        if (key !== 'Content-Type') { // Skip Content-Type as it's set automatically for FormData
          xhr.setRequestHeader(key, value);
        }
      });
      
      xhr.withCredentials = true;
      xhr.send(formData);
    });
  },
  generateFromImages: async (filenames, {
    onProgress = () => {},
    onMessage = () => {},
    timeout = 120000 // 2 minute timeout
  } = {}) => {
    try {
      // Create a query string with the filenames
      const params = new URLSearchParams();
      filenames.forEach(filename => params.append('filenames', filename));
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(`${API_BASE_URL}/api/generate_from_images?${params.toString()}`, {
        method: 'GET',
        credentials: 'include',
        headers: getDefaultHeaders(),
        signal: controller.signal
      });

      if (!response.ok) {
        clearTimeout(timeoutId);
        throw new Error(`Failed to generate from images: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let questions = [];
      let totalQuestions = 0;

      try {
        onMessage('Starting image processing...');
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          
          // Process complete SSE blocks separated by double newline
          const blocks = buffer.split("\n\n");
          buffer = blocks.pop() || '';

          for (const block of blocks) {
            const lines = block.split("\n");
            let eventType = '';
            let dataLine = '';
            for (const line of lines) {
              if (line.startsWith('event: ')) {
                eventType = line.replace('event: ', '').trim();
              } else if (line.startsWith('data: ')) {
                dataLine = line.replace('data: ', '').trim();
              }
            }

            if (!eventType || !dataLine) continue;

            try {
              const data = JSON.parse(dataLine);
              switch (eventType) {
                case 'start':
                  onMessage(data.message || 'Processing images...');
                  break;

                case 'total':
                  totalQuestions = data.count;
                  onProgress({
                    completed: 0,
                    total: totalQuestions,
                    message: `Found ${totalQuestions} questions to process`
                  });
                  break;

                case 'progress':
                  onProgress({
                    completed: data.count,
                    total: totalQuestions || data.total || data.count,
                    message: `Processing question ${data.count} of ${totalQuestions || data.total || data.count}`
                  });
                  break;

                case 'result':
                  if (data.questions && Array.isArray(data.questions)) {
                    questions = data.questions.map((q, index) => {
                      const optionsArray = Array.isArray(q.options);
                      const options = {
                        a: optionsArray ? q.options[0] : (q.options.A || q.options.a || ''),
                        b: optionsArray ? q.options[1] : (q.options.B || q.options.b || ''),
                        c: optionsArray ? q.options[2] : (q.options.C || q.options.c || ''),
                        d: optionsArray ? q.options[3] : (q.options.D || q.options.d || '')
                      };
                      const answer = (q.correct_answer || q.correctAnswer || q.answer || '').toLowerCase();
                      return {
                        id: Date.now() + index,
                        question: q.question || '',
                        options,
                        answer,
                        isEditing: false
                      };
                    });
                    clearTimeout(timeoutId);
                    return questions;
                  }
                  break;

                case 'error':
                  throw new Error(data.message || 'Failed to process images');

                default:
                  console.warn(`Unhandled event type: ${eventType}`);
                  break;
              }
            } catch (parseError) {
              console.error('Error parsing event data:', parseError);
              continue;
            }
          }
        }

        if (questions.length === 0) {
          throw new Error('No questions could be extracted from the images');
        }

        return questions;
      } finally {
        clearTimeout(timeoutId);
        reader.releaseLock();
      }
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
}