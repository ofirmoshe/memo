# Network Troubleshooting Guide for Memo App

This guide will help you troubleshoot network connectivity issues between your Expo app and the backend server.

## Understanding the Problem

When running the Expo app on your phone while the backend runs in a Docker container on your PC, there are several potential connectivity issues:

1. **Different Networks**: Your phone and PC might be on different networks
2. **Firewall Issues**: Your PC's firewall might block incoming connections
3. **Docker Network**: The Docker container might not be accessible from outside
4. **ngrok Configuration**: The ngrok tunnel might not be set up correctly

## Using the Connection Test Component

The app now includes a Connection Test component on the home screen that can help diagnose issues:

1. **Basic Test**: Tap "Test Connection" to check if the app can reach the backend
2. **Detailed View**: Tap "Show details" to see more information about the connection
3. **Test All Environments**: Test all configured API environments to see which ones work

## Common Solutions

### 1. Using ngrok (Recommended for Mobile Testing)

ngrok creates a secure tunnel to your local server, making it accessible from anywhere.

#### Setup:

1. Install ngrok from [https://ngrok.com/download](https://ngrok.com/download)
2. Run the automated script:

```powershell
# From the project root
cd MemoApp
node scripts/update-ngrok-url.js <your-ngrok-url>
```

Or use the PowerShell script:

```powershell
# From the project root
cd MemoApp
.\scripts\start-ngrok.ps1
```

3. Make sure `CURRENT_API_ENV` is set to `'TUNNEL'` in `src/config.ts`

### 2. Using Local Network IP (Same Network)

If your phone and PC are on the same network:

1. Find your PC's local IP address:
   - Windows: Run `ipconfig` in Command Prompt and look for IPv4 Address
   - Mac/Linux: Run `ifconfig` in Terminal and look for inet

2. Update the `LOCAL_NETWORK` URL in `src/config.ts`:

```typescript
LOCAL_NETWORK: 'http://YOUR_PC_IP_ADDRESS:8000', // e.g., 'http://192.168.1.100:8000'
```

3. Change `CURRENT_API_ENV` to `'LOCAL_NETWORK'` in `src/config.ts`

### 3. Check Docker Configuration

Make sure your Docker container exposes the correct port:

1. Check if the container is running: `docker ps`
2. Verify port mapping: The output should show something like `0.0.0.0:8000->8000/tcp`
3. If needed, restart the container with proper port mapping:

```bash
docker-compose down
docker-compose up -d
```

## Debugging Tips

1. **Check Server Logs**: Look at your Docker container logs for any errors
   ```bash
   docker logs <container_id>
   ```

2. **Test API Directly**: Use a tool like Postman or curl to test the API directly
   ```bash
   curl http://localhost:8000/health
   ```

3. **Check Firewall Settings**: Make sure your firewall allows connections on port 8000

4. **Verify ngrok Status**: Make sure your ngrok tunnel is active and note the URL

5. **Try Different Environments**: Switch between different API environments in `src/config.ts`

## Still Having Issues?

If you're still experiencing connectivity problems after trying these solutions:

1. Check if the backend server is functioning correctly
2. Verify that your Docker container is healthy
3. Try restarting both the backend server and the Expo app
4. Consider using a different port if 8000 is blocked 