/**
 * VellumProvider
 * ==============
 *
 * Root context provider for the Vellum UI SDK.
 * Wraps the entire application (or a subtree) to provide theme and API configuration.
 *
 * Usage:
 *   <VellumProvider theme={myTheme} apiConfig={myApiConfig}>
 *     <App />
 *   </VellumProvider>
 */

import { createContext, useContext, type ReactNode } from 'react';
import { ThemeProvider } from '@emotion/react';
import type { VellumTheme } from './theme';
import type { VellumApiConfig } from './api';

interface VellumContextValue {
  theme: VellumTheme;
  apiConfig: VellumApiConfig;
}

const VellumContext = createContext<VellumContextValue | null>(null);

export interface VellumProviderProps {
  theme: VellumTheme;
  apiConfig: VellumApiConfig;
  children: ReactNode;
}

export function VellumProvider({ theme, apiConfig, children }: VellumProviderProps) {
  return (
    <VellumContext.Provider value={{ theme, apiConfig }}>
      <ThemeProvider theme={theme}>
        {children}
      </ThemeProvider>
    </VellumContext.Provider>
  );
}

/**
 * Hook to access the Vellum context (theme + API config).
 * Throws if used outside a VellumProvider.
 */
export function useVellum(): VellumContextValue {
  const ctx = useContext(VellumContext);
  if (!ctx) {
    throw new Error('useVellum must be used within a <VellumProvider>');
  }
  return ctx;
}

/**
 * Hook to access just the API config.
 */
export function useVellumApi(): VellumApiConfig {
  return useVellum().apiConfig;
}

/**
 * Hook to access just the theme.
 */
export function useVellumTheme(): VellumTheme {
  return useVellum().theme;
}
