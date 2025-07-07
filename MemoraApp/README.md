# Memora Mobile App

A modern, AI-powered personal memory assistant for iOS and Android, built with React Native and Expo.

## Features

- **Chat Interface**: Natural conversation with your AI memory assistant
- **Content Saving**: Save text notes, URLs, images, and documents
- **Smart Search**: AI-powered semantic search through your memories
- **Browse Memories**: Pinterest-style grid view with filtering by content type
- **User Profile**: View statistics and manage account settings
- **Cross-Platform**: Works on both iOS and Android

## Design

- Pure black and white monochromatic theme
- Modern, futuristic UI inspired by top tech companies
- Smooth animations and transitions
- Responsive design optimized for mobile

## Prerequisites

- Node.js (v16 or higher)
- Expo CLI (`npm install -g @expo/cli`)
- iOS Simulator (for iOS development) or Android Studio (for Android development)
- Expo Go app on your physical device (for testing)

## Installation

1. **Clone the repository**
   ```bash
   git clone [your-repo-url]
   cd MemoraApp
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure backend URL**
   - Update the `BACKEND_URL` in `src/services/api.ts` with your Railway deployment URL
   - Or set it via Expo configuration

4. **Start the development server**
   ```bash
   npm start
   ```

## Development

### Running on iOS
```bash
npm run ios
```

### Running on Android
```bash
npm run android
```

### Running on Web
```bash
npm run web
```

### Testing on Physical Device
1. Install Expo Go from the App Store or Google Play
2. Scan the QR code from the terminal/browser
3. The app will load on your device

## Backend Integration

The app connects to the Memora backend API deployed on Railway. Make sure to:

1. Update the `BACKEND_URL` in `src/services/api.ts`
2. Ensure your backend is running and accessible
3. The backend should have CORS configured for your app domain

## Authentication

Currently uses device-based authentication with a simple user ID system. The app is designed to easily integrate Google and Apple sign-in later:

- Modular auth context
- Support for multiple auth providers
- Secure token storage with Expo SecureStore

## Project Structure

```
MemoraApp/
├── src/
│   ├── components/       # Reusable UI components
│   ├── screens/          # Main app screens
│   ├── contexts/         # React contexts (Auth, etc.)
│   ├── services/         # API and external services
│   ├── config/           # App configuration and theme
│   └── utils/            # Utility functions
├── assets/               # Images, fonts, etc.
├── App.tsx              # Main app component
└── package.json         # Dependencies and scripts
```

## Key Components

- **ChatScreen**: Main chat interface with Memora AI
- **BrowseScreen**: Pinterest-style memory browser
- **ProfileScreen**: User profile and settings
- **AuthContext**: Authentication state management
- **ApiService**: Backend API integration
- **Theme**: Consistent styling and colors

## Customization

### Colors
Update `src/config/theme.ts` to modify the color scheme:
```typescript
colors: {
  primary: '#000000',
  secondary: '#FFFFFF',
  background: '#000000',
  // ... other colors
}
```

### API Configuration
Update `src/services/api.ts` to modify backend endpoints or add new API calls.

## Building for Production

### iOS
```bash
expo build:ios
```

### Android
```bash
expo build:android
```

## Future Enhancements

- Google and Apple sign-in integration
- Push notifications
- Offline mode with local storage
- Voice messages
- Advanced search filters
- Export/import functionality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions, please create an issue in the repository or contact the development team. 