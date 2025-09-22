import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  Switch,
  SafeAreaView,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { apiService, UserStats as ApiUserStats } from '../services/api';
import { Logo } from '../components/Logo';

interface UserStats {
  totalMemories: number;
  textNotes: number;
  links: number;
  images: number;
  documents: number;
  topTags: Array<{ tag: string; count: number }>;
}

export const ProfileScreen: React.FC = () => {
  const { theme, isDarkMode, toggleTheme } = useTheme();
  const { user, signOut } = useAuth();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadUserStats = async () => {
      if (!user) return;
      
      try {
        const apiStats = await apiService.getUserStats(user.id);
        const mappedStats: UserStats = {
          totalMemories: apiStats.total_items,
          textNotes: apiStats.texts,
          links: apiStats.urls,
          images: apiStats.images,
          documents: apiStats.documents,
          topTags: apiStats.top_tags.map(([tag, count]) => ({ tag, count })),
        };
        setStats(mappedStats);
      } catch (error) {
        console.error('Error loading user stats:', error);
        Alert.alert('Error', 'Failed to load user statistics.');
      } finally {
        setIsLoading(false);
      }
    };

    loadUserStats();
  }, [user]);

  const handleSignOut = async () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: async () => {
            try {
              await signOut();
            } catch (error) {
              console.error('Sign out error:', error);
              Alert.alert('Error', 'Failed to sign out. Please try again.');
            }
          },
        },
      ]
    );
  };

  const StatCard = ({ label, value }: { label: string; value: number | string }) => (
    <View style={[styles.statCard, { backgroundColor: theme.colors.surface }]}>
      <Text style={[styles.statValue, { color: theme.colors.text }]}>{value}</Text>
      <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>{label}</Text>
    </View>
  );

  const SettingsRow = ({ label, children, isLast = false }: { label: string; children: React.ReactNode, isLast?: boolean }) => (
    <View style={[styles.settingsRow, { borderBottomColor: theme.colors.border, borderBottomWidth: isLast ? 0 : 1 }]}>
      <Text style={[styles.settingsLabel, { color: theme.colors.text }]}>{label}</Text>
      <View style={styles.settingsAction}>
        {children}
      </View>
    </View>
  );

  if (isLoading) {
    return (
      <SafeAreaView style={[styles.loadingContainer, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.userInfo}>
          <Logo size={48} color={theme.colors.primary} />
          <Text style={[styles.appName, { color: theme.colors.text }]}>Memora</Text>
          <Text style={[styles.userDescription, { color: theme.colors.textSecondary }]}>
            Your personal memory assistant
          </Text>
          
          {/* User Profile Info */}
          <View style={[styles.userProfileCard, { backgroundColor: theme.colors.surface }]}>
            <Text style={[styles.userName, { color: theme.colors.text }]}>
              {user?.name || 'User'}
            </Text>
            {user?.email && (
              <Text style={[styles.userEmail, { color: theme.colors.textSecondary }]}>
                {user.email}
              </Text>
            )}
            <Text style={[styles.userProvider, { color: theme.colors.textTertiary }]}>
              Signed in with {user?.provider === 'google' ? 'Google' : 'Guest Mode'}
            </Text>
          </View>
      </View>
      
          <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>Statistics</Text>
            <View style={styles.statsGrid}>
            <StatCard label="Total Memories" value={stats?.totalMemories || 0} />
            <StatCard label="Text Notes" value={stats?.textNotes || 0} />
            <StatCard label="Links" value={stats?.links || 0} />
            <StatCard label="Images" value={stats?.images || 0} />
            <StatCard label="Documents" value={stats?.documents || 0} />
            </View>
          </View>
          
        {stats?.topTags && stats.topTags.length > 0 && (
            <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>Top Tags</Text>
            <View style={styles.tagsContainer}>
              {stats.topTags.slice(0, 10).map((tagData, index) => (
                <View key={index} style={[styles.tagBadge, { backgroundColor: theme.colors.surface }]}>
                  <Text style={[styles.tagText, { color: theme.colors.text }]}>{tagData.tag}</Text>
                  <Text style={[styles.tagCount, { color: theme.colors.textSecondary }]}>{tagData.count}</Text>
                  </View>
                ))}
              </View>
            </View>
      )}

      <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>Settings</Text>
        <View style={[styles.settingsContainer, { backgroundColor: theme.colors.surface }]}>
          <SettingsRow label="Dark Mode">
            <Switch
              value={isDarkMode}
              onValueChange={toggleTheme}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
                thumbColor={theme.colors.background}
            />
          </SettingsRow>
          </View>
        </View>

        {/* Sign Out Button */}
        <View style={styles.section}>
          <TouchableOpacity
            style={[styles.signOutButton, { backgroundColor: theme.colors.error }]}
            onPress={handleSignOut}
            activeOpacity={0.8}
          >
            <Text style={styles.signOutButtonText}>Sign Out</Text>
          </TouchableOpacity>
        </View>
    </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  userInfo: {
    alignItems: 'center',
    paddingVertical: 24,
    marginBottom: 8,
  },
  userProfileCard: {
    padding: 16,
    borderRadius: 12,
    marginTop: 16,
    alignItems: 'center',
    width: '100%',
  },
  userName: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 14,
    marginBottom: 4,
  },
  userProvider: {
    fontSize: 12,
    textTransform: 'capitalize',
  },
  section: {
    marginVertical: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statCard: {
    width: '48%',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    textAlign: 'center',
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  tagBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  tagText: {
    fontSize: 14,
    fontWeight: '500',
    marginRight: 4,
  },
  tagCount: {
    fontSize: 12,
    fontWeight: '600',
  },
  settingsContainer: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  settingsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  settingsLabel: {
    fontSize: 16,
    fontWeight: '500',
  },
  settingsAction: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  appName: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 12,
    marginBottom: 4,
  },
  userDescription: {
    fontSize: 16,
    textAlign: 'center',
  },
  signOutButton: {
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  signOutButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});