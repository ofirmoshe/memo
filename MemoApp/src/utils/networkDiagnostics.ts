import axios from 'axios';
import { API_ENVIRONMENTS, CURRENT_API_ENV, config } from '../config';

export interface DiagnosticResult {
  success: boolean;
  latency?: number;
  statusCode?: number;
  errorType?: string;
  errorMessage?: string;
  responseData?: any;
}

/**
 * Tests the connection to a specific API endpoint
 * @param endpoint The API endpoint to test (e.g. '/health')
 * @param apiEnv The API environment to use (defaults to current environment)
 * @returns A promise that resolves to a DiagnosticResult
 */
export const testEndpoint = async (
  endpoint: string = '/health',
  apiEnv: keyof typeof API_ENVIRONMENTS = CURRENT_API_ENV
): Promise<DiagnosticResult> => {
  const startTime = Date.now();
  const url = `${API_ENVIRONMENTS[apiEnv]}${endpoint}`;
  
  try {
    const response = await axios.get(url, {
      timeout: config.api.timeoutMs,
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });
    
    const latency = Date.now() - startTime;
    return {
      success: true,
      latency,
      statusCode: response.status,
      responseData: response.data
    };
  } catch (error) {
    const latency = Date.now() - startTime;
    let result: DiagnosticResult = {
      success: false,
      latency
    };
    
    if (axios.isAxiosError(error)) {
      if (error.code === 'ECONNABORTED') {
        result.errorType = 'Timeout';
        result.errorMessage = 'Connection timed out';
      } else if (error.code === 'ERR_NETWORK') {
        result.errorType = 'Network';
        result.errorMessage = 'Network error';
      } else if (error.response) {
        result.errorType = `HTTP ${error.response.status}`;
        result.errorMessage = `${error.response.status} ${error.response.statusText}`;
        result.statusCode = error.response.status;
      } else if (error.request) {
        result.errorType = 'No Response';
        result.errorMessage = 'No response received from server';
      } else {
        result.errorType = 'Request Setup';
        result.errorMessage = error.message;
      }
    } else {
      result.errorType = 'Unknown';
      result.errorMessage = String(error);
    }
    
    return result;
  }
};

/**
 * Tests all configured API environments
 * @returns A promise that resolves to a record of environment names to diagnostic results
 */
export const testAllEnvironments = async (): Promise<Record<string, DiagnosticResult>> => {
  const results: Record<string, DiagnosticResult> = {};
  
  for (const env of Object.keys(API_ENVIRONMENTS) as Array<keyof typeof API_ENVIRONMENTS>) {
    try {
      results[env] = await testEndpoint('/health', env);
    } catch (error) {
      results[env] = {
        success: false,
        errorType: 'Test Failed',
        errorMessage: String(error)
      };
    }
  }
  
  return results;
};

/**
 * Gets common troubleshooting tips for network issues
 * @param errorType The type of error encountered
 * @returns An array of troubleshooting tips
 */
export const getTroubleshootingTips = (errorType?: string): string[] => {
  const commonTips = [
    'Ensure your Docker container is running (docker ps)',
    'Check if your phone and PC are on the same network',
    'Try restarting the ngrok tunnel',
  ];
  
  if (!errorType) return commonTips;
  
  switch (errorType) {
    case 'Timeout':
      return [
        'The server is taking too long to respond',
        'Check if your Docker container is overloaded',
        'Try restarting your Docker container',
        'Check your network connection speed',
        ...commonTips
      ];
    case 'Network':
      return [
        'Check if ngrok is running correctly',
        'Verify the ngrok URL in config.ts is up-to-date',
        'Try using a different API environment (LOCAL_NETWORK)',
        'Check your phone\'s internet connection',
        ...commonTips
      ];
    case 'No Response':
      return [
        'The server received the request but did not respond',
        'Check if your Docker container is functioning properly',
        'Try restarting your Docker container',
        'Check if the server endpoint exists',
        ...commonTips
      ];
    default:
      if (errorType.startsWith('HTTP')) {
        return [
          'The server returned an error status code',
          'Check server logs for more details',
          'Verify that your API endpoint is correct',
          ...commonTips
        ];
      }
      return commonTips;
  }
}; 