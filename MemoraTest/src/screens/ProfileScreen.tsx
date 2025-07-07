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
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { apiService, UserStats as ApiUserStats } from '../services/api';

const USER_ID = '831447258';

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
  const [stats, setStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadUserStats = async () => {
      try {
        const apiStats = await apiService.getUserStats(USER_ID);
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
  }, []);

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
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <View style={[styles.avatar, { backgroundColor: theme.colors.surface }]}>
          <Text style={[styles.avatarText, { color: theme.colors.text }]}>M</Text>
        </View>
        <Text style={[styles.userName, { color: theme.colors.text }]}>Memora User</Text>
        <Text style={[styles.userHandle, { color: theme.colors.textTertiary }]}>ID: {USER_ID}</Text>
      </View>
      
      {stats && (
        <>
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.colors.textSecondary }]}>Overview</Text>
            <View style={styles.statsGrid}>
              <StatCard label="Total" value={stats.totalMemories} />
              <StatCard label="Notes" value={stats.textNotes} />
              <StatCard label="Links" value={stats.links} />
              <StatCard label="Images" value={stats.images} />
            </View>
          </View>
          
          {stats.topTags.length > 0 && (
            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.colors.textSecondary }]}>Top Tags</Text>
              <View style={[styles.tagsContainer, { backgroundColor: theme.colors.surface }]}>
                {stats.topTags.slice(0, 5).map((tag, index) => (
                  <View key={index} style={[styles.tag, { borderBottomColor: theme.colors.border, borderBottomWidth: index === Math.min(stats.topTags.length, 5) - 1 ? 0 : 1 }]}>
                    <Text style={[styles.tagText, { color: theme.colors.text }]}>{tag.tag}</Text>
                    <Text style={[styles.tagCount, { color: theme.colors.textSecondary }]}>{tag.count}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}
        </>
      )}

      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.colors.textSecondary }]}>Preferences</Text>
        <View style={[styles.settingsContainer, { backgroundColor: theme.colors.surface }]}>
          <SettingsRow label="Dark Mode">
            <Switch
              value={isDarkMode}
              onValueChange={toggleTheme}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
              thumbColor={isDarkMode ? theme.colors.surface : '#f4f3f4'}
            />
          </SettingsRow>
          <SettingsRow label="Notifications">
            <Switch disabled />
          </SettingsRow>
          <SettingsRow label="Language" isLast={true}>
            <Text style={[styles.languageText, { color: theme.colors.textTertiary }]}>English</Text>
          </SettingsRow>
        </View>
      </View>

      <TouchableOpacity style={styles.signOutButton}>
        <Text style={[styles.signOutText, { color: theme.colors.error }]}>Sign Out</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  container: { flex: 1 },
  header: { alignItems: 'center', paddingVertical: 32, paddingHorizontal: 16 },
  avatar: { width: 100, height: 100, borderRadius: 50, justifyContent: 'center', alignItems: 'center', marginBottom: 16 },
  avatarText: { fontSize: 48, fontWeight: '300' },
  userName: { fontSize: 28, fontWeight: '600', marginBottom: 4 },
  userHandle: { fontSize: 16, color: 'grey' },
  section: { marginBottom: 24, paddingHorizontal: 16 },
  sectionTitle: { fontSize: 14, fontWeight: '600', textTransform: 'uppercase', marginBottom: 12, letterSpacing: 0.5 },
  statsGrid: { flexDirection: 'row', justifyContent: 'space-between' },
  statCard: { width: '23%', alignItems: 'center', paddingVertical: 16, borderRadius: 12 },
  statValue: { fontSize: 24, fontWeight: '700', marginBottom: 4 },
  statLabel: { fontSize: 12, textTransform: 'uppercase', fontWeight: '500' },
  tagsContainer: { borderRadius: 12, paddingHorizontal: 16 },
  tag: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 14 },
  tagText: { fontSize: 16, fontWeight: '500' },
  tagCount: { fontSize: 16 },
  settingsContainer: { borderRadius: 12, overflow: 'hidden' },
  settingsRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, paddingHorizontal: 16 },
  settingsLabel: { flex: 1, fontSize: 16, fontWeight: '500' },
  settingsAction: {},
  languageText: { fontSize: 16 },
  signOutButton: { marginHorizontal: 16, borderRadius: 12, padding: 16, alignItems: 'center', marginBottom: 48, backgroundColor: '#1e1e1e' },
  signOutText: { fontSize: 16, fontWeight: '600' },
});