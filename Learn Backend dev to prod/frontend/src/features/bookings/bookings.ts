import { queryOptions, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../../lib/api/client'

export type BookingStatus = 'CONFIRMED' | 'CANCELLED' | 'COMPLETED'

export type Booking = {
  id: string
  room_id: string
  user_id: string
  room_name: string | null
  start_time: string
  end_time: string
  purpose: string | null
  status: BookingStatus
  created_at: string
}

export type AvailabilityBooking = {
  start_time: string
  end_time: string
  status: BookingStatus
}

export const BOOKINGS_KEY = ['bookings'] as const

export const bookingsQuery = queryOptions({
  queryKey: BOOKINGS_KEY,
  queryFn: async (): Promise<Booking[]> =>
    (await api.get<{ data: Booking[] }>('/bookings')).data.data,
})

export const availabilityQuery = (roomId: string, day: string) =>
  queryOptions({
    queryKey: ['availability', roomId, day],
    queryFn: async (): Promise<AvailabilityBooking[]> =>
      (
        await api.get<{ data: { bookings: AvailabilityBooking[] } }>(
          `/rooms/${roomId}/availability`,
          { params: { day } },
        )
      ).data.data.bookings,
  })

export function useBookings() {
  return useQuery(bookingsQuery)
}

export function useAvailability(roomId: string, day: string) {
  return useQuery(availabilityQuery(roomId, day))
}

export function useCreateBooking(roomId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { start_time: string; end_time: string; purpose: string | null }) =>
      (
        await api.post<{ data: Booking }>('/bookings', {
          room_id: roomId,
          start_time: input.start_time,
          end_time: input.end_time,
          purpose: input.purpose,
        })
      ).data.data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BOOKINGS_KEY })
      queryClient.invalidateQueries({ queryKey: ['availability'] })
    },
  })
}

export function useCancelBooking() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (bookingId: string) => api.delete(`/bookings/${bookingId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BOOKINGS_KEY })
      queryClient.invalidateQueries({ queryKey: ['availability'] })
    },
  })
}
