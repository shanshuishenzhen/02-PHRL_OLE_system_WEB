export const getToken = (): string => {
  return localStorage.getItem('token') || ''
}

export const setToken = (token: string): void => {
  localStorage.setItem('token', token)
}

export const clearToken = (): void => {
  localStorage.removeItem('token')
}

export interface User {
  id: string
  username: string
  role: 'admin' | 'teacher' | 'student'
}

interface AuthResponse {
  token?: string
  user?: User
  [key: string]: unknown
}

export const login = async (username: string, password: string): Promise<User> => {
  const response = await axios.post<AuthResponse>('/api/auth/login', { username, password })
  if (response.data.token) {
    setToken(response.data.token)
  }
  if (!response.data.user) {
    throw new Error('Invalid login response')
  }
  return response.data.user
}

export const importUsers = async (users: Array<{username: string, password: string, role: string}>): Promise<void> => {
  await axios.post<void>('/api/auth/import', { users })
}

export const getCurrentUser = async (): Promise<User> => {
  const response = await axios.get<{user: User}>('/api/auth/me')
  return response.data.user
}

export const checkPermission = (requiredRole: User['role']): boolean => {
  const token = getToken()
  if (!token) return false
  // 实际实现需要解析JWT token中的角色信息
  return true
}

export const listAllUsers = async (): Promise<User[]> => {
  const response = await axios.get<{users: User[]}>('/api/auth/users')
  return response.data.users
}