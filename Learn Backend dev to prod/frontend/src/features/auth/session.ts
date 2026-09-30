import { queryOptions, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../../lib/api/client'
import { toApiError } from '../../lib/api/errors'

export type SessionUser = {
  id: string
  name: string
  email: string
  roles: string[]
}

export const SESSION_KEY = ['session'] as const

export const sessionQuery = queryOptions({
  queryKey: SESSION_KEY,
  queryFn: async (): Promise<SessionUser | null> => {
    try {
      const { data } = await api.get<{ data: SessionUser }>('/auth/me')
      return data.data
    } catch (error) {
      // "not signed in" is a normal answer, not a failure worth caching as an error
      if (toApiError(error).isUnauthorized) return null
      throw error
    }
  },
  staleTime: 60_000,
})

export function useSession() {
  return useQuery(sessionQuery)
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { email: string; password: string }) => {
      const { data } = await api.post<{ data: { user: SessionUser } }>('/auth/login', input)
      return data.data.user
    },
    onSuccess: (user) => queryClient.setQueryData(SESSION_KEY, user),
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => api.post('/auth/logout'),
    onSettled: () => queryClient.setQueryData(SESSION_KEY, null),
  })
}
