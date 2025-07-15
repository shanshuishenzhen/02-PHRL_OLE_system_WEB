export const getToken = (): string => {
  return localStorage.getItem('token') || ''
}

export const setToken = (token: string): void => {
  localStorage.setItem('token', token)
}

export const clearToken = (): void => {
  localStorage.removeItem('token')
}