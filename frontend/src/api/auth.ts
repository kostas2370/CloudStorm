import { api } from './axios';
import { ENDPOINTS } from './endpoints';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  tokens: {
    access: string;
    refresh: string;
  };
}

export async function login(
  credentials: LoginCredentials
): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>(ENDPOINTS.AUTH.LOGIN, credentials);
  return data;
}
