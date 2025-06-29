// Environment configuration for API access
export const API_ENVIRONMENTS = {
  LOCAL: 'http://localhost:8000',
  
  // For testing in Expo Go on a physical device (on the same network)
  // Replace with your PC's local network IP address
  LOCAL_NETWORK: 'http://192.168.1.100:8000', // Update this with your actual local IP
  
  // For testing with ngrok tunnel
  // IMPORTANT: Update this whenever ngrok provides a new URL
  TUNNEL: 'https://8c3d-93-172-168-15.ngrok-free.app',
  
  // For testing with 10.0.2.2 (Android Emulator special IP that points to host's localhost)
  ANDROID_EMULATOR: 'http://10.0.2.2:8000',
};

// Select which environment to use
export const CURRENT_API_ENV = 'LOCAL'; // Options: 'LOCAL', 'LOCAL_NETWORK', 'TUNNEL', 'ANDROID_EMULATOR'

export const config = {
  api: {
    baseUrl: API_ENVIRONMENTS[CURRENT_API_ENV],
    useDemoData: false, // Set to false to use real API
    timeoutMs: 10000, // 10 seconds timeout for API requests
  },
  demo: {
    delay: 500, // Simulate network delay in ms
  },
}; 