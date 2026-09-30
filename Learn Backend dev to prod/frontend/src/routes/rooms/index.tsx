import { Link, createRoute } from '@tanstack/react-router'

import { buttonVariants } from '../../components/ui/button'
import { isAdmin } from '../../features/auth/guard'
import { useRooms } from '../../features/rooms/rooms'
import { Route as appRoute, Loading } from '../app'

export const Route = createRoute({
  getParentRoute: () => appRoute,
  path: '/rooms',
  component: RoomsPage,
  pendingComponent: Loading,
})

function statusBadge(status: string) {
  return (
    <span
      className={
        status === 'ACTIVE'
          ? 'rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-foreground'
          : 'rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground'
      }
    >
      {status}
    </span>
  )
}

function RoomsPage() {
  const { user } = Route.useRouteContext()
  const { data: rooms, isPending, isError, error } = useRooms()

  return (
    <>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Rooms</h1>
        {isAdmin(user) && (
          <Link to="/rooms/new" className={buttonVariants({ size: 'sm' })}>
            New room
          </Link>
        )}
      </div>

      {isPending && <p className="mt-6 text-sm text-muted-foreground">Loading rooms…</p>}

      {isError && (
        <p role="alert" className="mt-6 text-sm text-destructive">
          {error.message}
        </p>
      )}

      {rooms && rooms.length === 0 && (
        <p className="mt-6 text-sm text-muted-foreground">No rooms yet.</p>
      )}

      {rooms && rooms.length > 0 && (
        <ul className="mt-6 flex flex-col gap-2">
          {rooms.map((room) => (
            <li key={room.id}>
              <Link
                to="/rooms/$roomId"
                params={{ roomId: room.id }}
                className="flex items-center justify-between rounded-md border border-border px-4 py-3 hover:bg-muted"
              >
                <span className="flex flex-col">
                  <span className="text-sm font-medium">{room.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {room.location} · seats {room.capacity}
                    {room.description ? ` · ${room.description}` : ''}
                  </span>
                </span>
                {statusBadge(room.status)}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
