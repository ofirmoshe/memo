// Environment configuration for API access
export const API_ENVIRONMENTS = {
  LOCAL: 'http://localhost:8000',
  LOCAL_NETWORK: 'http://YOUR_PC_IP_ADDRESS:8000', // Replace with your PC's local IP (e.g. 192.168.1.100)
  
  // IMPORTANT: Replace this with your actual ngrok URL from the terminal output
  // Look for a line like: "Forwarding https://xxxx-xxx-xxx-xxx.ngrok-free.app -> http://localhost:8000"
  // Copy that URL (the https://xxxx-xxx-xxx-xxx.ngrok-free.app part) and paste it below
  TUNNEL: 'https://590c-2a00-a041-f1c6-e00-a55c-940b-2574-3165.ngrok-free.app', 
};

// Select which environment to use
export const CURRENT_API_ENV = 'TUNNEL'; // Change this to switch environments

export const config = {
  api: {
    baseUrl: API_ENVIRONMENTS[CURRENT_API_ENV],
    useDemoData: false, // Set to false to use real API
  },
  demo: {
    delay: 500, // Simulate network delay in ms
  },
}; 