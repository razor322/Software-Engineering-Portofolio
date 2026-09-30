import { queryOptions, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../../lib/api/client'

export type RoomStatus = 'ACTIVE' | 'INACTIVE'

export type Room = {
  id: string
  name: string
  description: string | null
  location: string
  capacity: number
  status: RoomStatus
  created_at: string
  updated_at: string
}

export type RoomInput = {
  name: string
  description: string | null
  location: string
  capacity: number
}

export const ROOMS_KEY = ['rooms'] as const

export const roomsQuery = queryOptions({
  queryKey: ROOMS_KEY,
  queryFn: async (): Promise<Room[]> => (await api.get<{ data: Room[] }>('/rooms')).data.data,
})

export const roomQuery = (roomId: string) =>
  queryOptions({
    queryKey: [...ROOMS_KEY, roomId],
    queryFn: async (): Promise<Room> => (await api.get<{ data: Room }>(`/rooms/${roomId}`)).data.data,
  })

export function useRooms() {
  return useQuery(roomsQuery)
}

export function useRoom(roomId: string) {
  return useQuery(roomQuery(roomId))
}

export function useCreateRoom() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: RoomInput) =>
      (await api.post<{ data: Room }>('/rooms', input)).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ROOMS_KEY }),
  })
}

export function useUpdateRoom(roomId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: Partial<RoomInput> & { status?: RoomStatus }) =>
      (await api.patch<{ data: Room }>(`/rooms/${roomId}`, input)).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ROOMS_KEY }),
  })
}

export function useDeleteRoom() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (roomId: string) => api.delete(`/rooms/${roomId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ROOMS_KEY }),
  })
}
