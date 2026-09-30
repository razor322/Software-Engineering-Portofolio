import { Link, createRoute } from '@tanstack/react-router'

import { Button } from '../../components/ui/button'
import { useBookings, useCancelBooking } from '../../features/bookings/bookings'
import { Route as appRoute, Loading } from '../app'

export const Route = createRoute({
  getParentRoute: () => appRoute,
  path: '/bookings',
  component: BookingsPage,
  pendingComponent: Loading,
})

function when(iso: string): string {
  return new Date(iso).toLocaleString([], {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function BookingsPage() {
  const { data: bookings, isPending, isError, error } = useBookings()
  const cancel = useCancelBooking()

  return (
    <>
      <h1 className="text-xl font-semibold">Bookings</h1>

      {isPending && <p className="mt-6 text-sm text-muted-foreground">Loading bookings…</p>}

      {isError && (
        <p role="alert" className="mt-6 text-sm text-destructive">
          {error.message}
        </p>
      )}

      {bookings && bookings.length === 0 && (
        <p className="mt-6 text-sm text-muted-foreground">
          Nothing booked yet. Pick a room to make your first booking.
        </p>
      )}

      {bookings && bookings.length > 0 && (
        <ul className="mt-6 flex flex-col gap-2">
          {bookings.map((booking) => (
            <li
              key={booking.id}
              className="flex items-center justify-between rounded-md border border-border px-4 py-3"
            >
              <span className="flex flex-col">
                <Link
                  to="/rooms/$roomId"
                  params={{ roomId: booking.room_id }}
                  className="text-sm font-medium hover:underline"
                >
                  {booking.room_name ?? 'Unknown room'}
                </Link>
                <span className="text-xs text-muted-foreground">
                  {when(booking.start_time)} → {when(booking.end_time)}
                  {booking.purpose ? ` · ${booking.purpose}` : ''}
                </span>
              </span>
              <span className="flex items-center gap-3">
                <span
                  className={
                    booking.status === 'CONFIRMED'
                      ? 'text-xs font-medium'
                      : 'text-xs font-medium text-muted-foreground'
                  }
                >
                  {booking.status}
                </span>
                {booking.status === 'CONFIRMED' && (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={cancel.isPending}
                    onClick={() => cancel.mutate(booking.id)}
                  >
                    Cancel
                  </Button>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
