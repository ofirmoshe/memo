import React, { useState, useEffect } from 'react';
import { View, Text, Button, StyleSheet } from 'react-native';
import axios from 'axios';
import { API_ENVIRONMENTS, CURRENT_API_ENV } from '../config';

export const ConnectionTest = () => {
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  
  const testConnection = async () => {
    setStatus('loading');
    setMessage('Testing connection to backend...');
    
    try {
      const response = await axios.get(`${API_ENVIRONMENTS[CURRENT_API_ENV]}/health`);
      setStatus('success');
      setMessage(`Connection successful! Server status: ${JSON.stringify(response.data)}`);
    } catch (error) {
      setStatus('error');
      if (axios.isAxiosError(error)) {
        setMessage(`Connection failed: ${error.message}`);
      } else {
        setMessage(`Connection failed: Unknown error`);
      }
    }
  };
  
  return (
    <View style={styles.container}>
      <Text style={styles.title}>API Connection Test</Text>
      <Text style={styles.subtitle}>Current API URL:</Text>
      <Text style={styles.url}>{API_ENVIRONMENTS[CURRENT_API_ENV]}</Text>
      
      <Button 
        title="Test Connection" 
        onPress={testConnection} 
      />
      
      {status !== 'idle' && (
        <View style={styles.resultContainer}>
          <Text style={[
            styles.statusText,
            status === 'loading' && styles.loading,
            status === 'success' && styles.success,
            status === 'error' && styles.error
          ]}>
            {message}
          </Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    marginVertical: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
  },
  url: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  resultContainer: {
    marginTop: 16,
    padding: 8,
    backgroundColor: '#fff',
    borderRadius: 4,
  },
  statusText: {
    fontSize: 14,
  },
  loading: {
    color: '#f90',
  },
  success: {
    color: '#090',
  },
  error: {
    color: '#d00',
  },
}); 