// Debug utility to check API responses
export const debugApiResponse = (endpoint, response, label = 'API Response') => {
  console.group(`🔍 ${label} - ${endpoint}`);
  console.log('Endpoint:', endpoint);
  console.log('Response Type:', typeof response);
  console.log('Is Array:', Array.isArray(response));
  console.log('Full Response:', response);

  if (response && typeof response === 'object') {
    console.log('Response Keys:', Object.keys(response));
  }

  console.groupEnd();
  return response;
};