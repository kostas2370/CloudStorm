import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { login as loginApi } from '../../api/auth';

const ACCESS_KEY = 'cloudstorm_access_token';
const REFRESH_KEY = 'cloudstorm_refresh_token';

export const getStoredTokens = (): { access: string; refresh: string } | null => {
  const access = localStorage.getItem(ACCESS_KEY);
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (access && refresh) return { access, refresh };
  return null;
};

const stored = getStoredTokens();

export interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  accessToken: stored?.access ?? null,
  refreshToken: stored?.refresh ?? null,
  isAuthenticated: !!stored,
  loading: false,
  error: null,
};

export const login = createAsyncThunk(
  'auth/login',
  async (
    credentials: { email: string; password: string },
    { rejectWithValue }
  ) => {
    try {
      const data = await loginApi(credentials);
      return data.tokens;
    } catch (err: unknown) {
      const message =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data
              ?.detail ?? 'Login failed'
          : 'Login failed';
      return rejectWithValue(message);
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout(state) {
      state.accessToken = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.error = null;
      localStorage.removeItem(ACCESS_KEY);
      localStorage.removeItem(REFRESH_KEY);
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers(builder) {
    builder
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(
        login.fulfilled,
        (state, action) => {
          state.loading = false;
          state.error = null;
          state.accessToken = action.payload.access;
          state.refreshToken = action.payload.refresh;
          state.isAuthenticated = true;
          localStorage.setItem(ACCESS_KEY, action.payload.access);
          localStorage.setItem(REFRESH_KEY, action.payload.refresh);
        }
      )
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = (action.payload as string) ?? 'Login failed';
      });
  },
});

export const { logout, clearError } = authSlice.actions;
export default authSlice.reducer;
