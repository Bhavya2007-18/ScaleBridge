export function getToken(): string | null {
  return localStorage.getItem('scalebridge_token');
}

export function setToken(token: string): void {
  localStorage.setItem('scalebridge_token', token);
}

export function clearToken(): void {
  localStorage.removeItem('scalebridge_token');
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
