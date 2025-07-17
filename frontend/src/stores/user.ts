import { defineStore } from 'pinia'

export interface UserState {
  id: string
  username: string
  role: 'admin' | 'teacher' | 'student' | 'marker' | null
  token: string | null
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    id: '',
    username: '',
    role: null,
    token: null
  }),

  actions: {
    setUser(user: Partial<UserState>) {
      Object.assign(this, user)
    },

    clearUser() {
      this.id = ''
      this.username = ''
      this.role = null
      this.token = null
    },

    isStudent() {
      return this.role === 'student'
    },

    isTeacher() {
      return this.role === 'teacher'
    },

    isAdmin() {
      return this.role === 'admin'
    },

    isMarker() {
      return this.role === 'marker'
    }
  }
})