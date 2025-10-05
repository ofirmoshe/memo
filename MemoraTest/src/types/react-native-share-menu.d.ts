declare module 'react-native-share-menu' {
  interface ShareData {
    mimeType: string;
    data: string;
    extraData?: any;
  }

  interface ShareMenuModule {
    getInitialShare(): Promise<ShareData | null>;
    addNewShareListener(listener: (data: ShareData) => void): void;
    clearNewShareListener(): void;
  }

  const ShareMenu: ShareMenuModule;
  export default ShareMenu;
} 