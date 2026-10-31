'use client';

import { create } from 'zustand';
import { apiRequest } from '@/lib/api';

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthModalOpen: boolean;
  authModalTab: 'login' | 'register';
  error: string | null;
  
  setAuthModalOpen: (open: boolean, tab?: 'login' | 'register') => void;
  initialize: () => Promise<void>;
  login: (email: string, password: string) => Promise<boolean>;
  register: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  refreshToken: null,
  isLoading: true,
  isAuthModalOpen: false,
  authModalTab: 'login',
  error: null,

  setAuthModalOpen: (open, tab = 'login') => {
    set({ isAuthModalOpen: open, authModalTab: tab, error: null });
  },

  clearError: () => set({ error: null }),

  initialize: async () => {
    if (typeof window === 'undefined') return;
    const token = localStorage.getItem('medirisk_token');
    const refreshToken = localStorage.getItem('medirisk_refresh_token');

    if (!token) {
      set({ isLoading: false });
      return;
    }

    set({ token, refreshToken });
    try {
      const user = await apiRequest<User>('/api/v1/auth/me');
      set({ user, isLoading: false });
    } catch {
      localStorage.removeItem('medirisk_token');
      localStorage.removeItem('medirisk_refresh_token');
      set({ user: null, token: null, refreshToken: null, isLoading: false });
    }
  },

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const res = await apiRequest<{
        access_token: string;
        refresh_token: string;
        user: User;
      }>('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      localStorage.setItem('medirisk_token', res.access_token);
      if (res.refresh_token) {
        localStorage.setItem('medirisk_refresh_token', res.refresh_token);
      }

      set({
        token: res.access_token,
        refreshToken: res.refresh_token || null,
        user: res.user,
        isLoading: false,
        isAuthModalOpen: false,
      });
      return true;
    } catch (err: any) {
      set({ error: err.message || 'Login failed', isLoading: false });
      return false;
    }
  },

  register: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      await apiRequest('/api/v1/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      // Automatically log in after registration
      return await get().login(email, password);
    } catch (err: any) {
      set({ error: err.message || 'Registration failed', isLoading: false });
      return false;
    }
  },

  logout: async () => {
    const refreshToken = get().refreshToken;
    try {
      if (refreshToken) {
        await apiRequest('/api/v1/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      }
    } catch {
      // ignore
    }

    localStorage.removeItem('medirisk_token');
    localStorage.removeItem('medirisk_refresh_token');
    set({ user: null, token: null, refreshToken: null });
  },
}));
