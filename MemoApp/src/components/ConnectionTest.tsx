import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, ScrollView } from 'react-native';
import { API_ENVIRONMENTS, CURRENT_API_ENV } from '../config';
import { testEndpoint, testAllEnvironments, getTroubleshootingTips, DiagnosticResult } from '../utils/networkDiagnostics';

export const ConnectionTest = () => {
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [expanded, setExpanded] = useState(false);
  const [details, setDetails] = useState<DiagnosticResult | null>(null);
  const [allResults, setAllResults] = useState<Record<string, DiagnosticResult> | null>(null);
  const [showAllTests, setShowAllTests] = useState(false);
  
  const testConnection = async () => {
    setStatus('loading');
    setMessage('Testing connection to backend...');
    setDetails(null);
    setAllResults(null);
    
    try {
      const result = await testEndpoint('/health');
      
      if (result.success) {
        setStatus('success');
        setMessage(`Connection successful (${result.latency}ms)`);
      } else {
        setStatus('error');
        setMessage(`Connection failed: ${result.errorMessage}`);
      }
      
      setDetails(result);
    } catch (error) {
      setStatus('error');
      setMessage(`Test failed: ${String(error)}`);
    }
  };
  
  const testAllConnections = async () => {
    setStatus('loading');
    setMessage('Testing all API environments...');
    setShowAllTests(true);
    
    try {
      const results = await testAllEnvironments();
      setAllResults(results);
      
      // Set overall status based on current environment result
      const currentResult = results[CURRENT_API_ENV];
      if (currentResult && currentResult.success) {
        setStatus('success');
        setMessage(`Current environment (${CURRENT_API_ENV}) is working`);
      } else {
        setStatus('error');
        setMessage(`Current environment (${CURRENT_API_ENV}) has issues`);
      }
    } catch (error) {
      setStatus('error');
      setMessage(`Tests failed: ${String(error)}`);
    }
  };

  // Auto-test on first render
  useEffect(() => {
    testConnection();
  }, []);
  
  const toggleExpanded = () => {
    setExpanded(!expanded);
    if (!expanded && !details) {
      testConnection();
    }
  };
  
  const renderEnvironmentResults = () => {
    if (!allResults) return null;
    
    return (
      <View style={styles.allResultsContainer}>
        <Text style={styles.subtitle}>All Environment Results:</Text>
        {Object.entries(allResults).map(([env, result]) => (
          <View 
            key={env} 
            style={[
              styles.envResultItem,
              result.success ? styles.successResult : styles.errorResult,
              env === CURRENT_API_ENV && styles.currentEnvResult
            ]}
          >
            <View style={styles.envResultHeader}>
              <Text style={[
                styles.envName,
                env === CURRENT_API_ENV && styles.currentEnvText
              ]}>
                {env} {env === CURRENT_API_ENV && '(CURRENT)'}
              </Text>
              <Text style={[
                styles.envStatus,
                result.success ? styles.success : styles.error
              ]}>
                {result.success ? '✓ OK' : '✗ Failed'}
              </Text>
            </View>
            
            <Text style={styles.envUrl}>{API_ENVIRONMENTS[env as keyof typeof API_ENVIRONMENTS]}</Text>
            
            {result.latency !== undefined && (
              <Text style={styles.detailText}>Latency: {result.latency}ms</Text>
            )}
            
            {!result.success && result.errorMessage && (
              <Text style={[styles.detailText, styles.error]}>
                Error: {result.errorType} - {result.errorMessage}
              </Text>
            )}
          </View>
        ))}
      </View>
    );
  };
  
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>API Connection Status</Text>
        <TouchableOpacity onPress={toggleExpanded}>
          <Text style={styles.expandButton}>{expanded ? 'Hide' : 'Show'} details</Text>
        </TouchableOpacity>
      </View>
      
      {expanded && (
        <View style={styles.detailsContainer}>
          <Text style={styles.subtitle}>Current API URL:</Text>
          <Text style={styles.url}>{API_ENVIRONMENTS[CURRENT_API_ENV]}</Text>
          
          <View style={styles.envContainer}>
            <Text style={styles.subtitle}>Available Environments:</Text>
            {Object.entries(API_ENVIRONMENTS).map(([key, url]) => (
              <Text key={key} style={[
                styles.envText,
                key === CURRENT_API_ENV && styles.activeEnv
              ]}>
                {key}: {url}
              </Text>
            ))}
          </View>
        </View>
      )}
      
      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={[
            styles.testButton,
            status === 'loading' && styles.loadingButton,
            status === 'success' && styles.successButton,
            status === 'error' && styles.errorButton
          ]}
          onPress={testConnection}
          disabled={status === 'loading'}
        >
          {status === 'loading' ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Text style={styles.buttonText}>
              {status === 'idle' ? 'Test Connection' : 
               status === 'success' ? 'Test Again' : 
               'Retry Connection'}
            </Text>
          )}
        </TouchableOpacity>
        
        {expanded && (
          <TouchableOpacity
            style={styles.allTestsButton}
            onPress={testAllConnections}
            disabled={status === 'loading'}
          >
            <Text style={styles.allTestsButtonText}>
              Test All Environments
            </Text>
          </TouchableOpacity>
        )}
      </View>
      
      {status !== 'idle' && (
        <View style={[
          styles.resultContainer,
          status === 'loading' && styles.loadingResult,
          status === 'success' && styles.successResult,
          status === 'error' && styles.errorResult
        ]}>
          <Text style={[
            styles.statusText,
            status === 'loading' && styles.loading,
            status === 'success' && styles.success,
            status === 'error' && styles.error
          ]}>
            {message}
          </Text>
          
          {expanded && details && !showAllTests && (
            <View style={styles.detailsData}>
              {details.latency !== undefined && (
                <Text style={styles.detailText}>Latency: {details.latency}ms</Text>
              )}
              {details.statusCode !== undefined && (
                <Text style={styles.detailText}>Status Code: {details.statusCode}</Text>
              )}
              {details.errorType && (
                <Text style={styles.detailText}>Error Type: {details.errorType}</Text>
              )}
              {details.responseData && (
                <Text style={styles.detailText}>
                  Response: {JSON.stringify(details.responseData, null, 2)}
                </Text>
              )}
            </View>
          )}
          
          {expanded && showAllTests && renderEnvironmentResults()}
        </View>
      )}
      
      {expanded && status === 'error' && details?.errorType && (
        <ScrollView style={styles.troubleshootContainer}>
          <Text style={styles.troubleshootTitle}>Troubleshooting Tips:</Text>
          {getTroubleshootingTips(details.errorType).map((tip, index) => (
            <Text key={index} style={styles.troubleshootItem}>• {tip}</Text>
          ))}
          
          {status === 'error' && (
            <>
              <Text style={styles.troubleshootTitle}>Try changing environments:</Text>
              <Text style={styles.troubleshootItem}>
                • Open MemoApp/src/config.ts and change CURRENT_API_ENV to 'LOCAL_NETWORK'
              </Text>
              <Text style={styles.troubleshootItem}>
                • Update the LOCAL_NETWORK URL with your PC's actual IP address
              </Text>
              <Text style={styles.troubleshootItem}>
                • Find your IP address by running 'ipconfig' (Windows) or 'ifconfig' (Mac/Linux)
              </Text>
            </>
          )}
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    marginVertical: 8,
    marginHorizontal: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  expandButton: {
    fontSize: 14,
    color: '#007AFF',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
  },
  url: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  detailsContainer: {
    marginBottom: 12,
    padding: 8,
    backgroundColor: '#fff',
    borderRadius: 4,
  },
  envContainer: {
    marginTop: 8,
  },
  envText: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  activeEnv: {
    fontWeight: 'bold',
    color: '#007AFF',
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
    gap: 10,
  },
  testButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    backgroundColor: '#007AFF',
    minWidth: 150,
    alignItems: 'center',
  },
  loadingButton: {
    backgroundColor: '#f90',
  },
  successButton: {
    backgroundColor: '#090',
  },
  errorButton: {
    backgroundColor: '#d00',
  },
  buttonText: {
    color: '#fff',
    fontWeight: '500',
  },
  allTestsButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
    alignItems: 'center',
  },
  allTestsButtonText: {
    color: '#007AFF',
    fontWeight: '500',
    fontSize: 12,
  },
  resultContainer: {
    padding: 12,
    backgroundColor: '#fff',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  loadingResult: {
    borderColor: '#f90',
  },
  successResult: {
    borderColor: '#090',
  },
  errorResult: {
    borderColor: '#d00',
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
  detailsData: {
    marginTop: 8,
    padding: 8,
    backgroundColor: '#f9f9f9',
    borderRadius: 4,
  },
  detailText: {
    fontSize: 12,
    color: '#666',
    fontFamily: 'monospace',
    marginBottom: 2,
  },
  troubleshootContainer: {
    marginTop: 12,
    padding: 12,
    maxHeight: 200,
    backgroundColor: '#fff',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderStyle: 'dashed',
  },
  troubleshootTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 6,
    marginTop: 8,
  },
  troubleshootItem: {
    fontSize: 12,
    color: '#333',
    marginBottom: 4,
  },
  allResultsContainer: {
    marginTop: 8,
  },
  envResultItem: {
    marginTop: 8,
    padding: 8,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  currentEnvResult: {
    borderWidth: 2,
  },
  envResultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  envName: {
    fontSize: 14,
    fontWeight: '500',
  },
  currentEnvText: {
    fontWeight: 'bold',
  },
  envStatus: {
    fontSize: 12,
    fontWeight: '500',
  },
  envUrl: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
}); 