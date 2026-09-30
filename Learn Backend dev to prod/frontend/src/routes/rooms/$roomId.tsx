import { useState } from 'react'
import { useNavigate, createRoute } from '@tanstack/react-router'

import { Button } from '../../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { isAdmin } from '../../features/auth/guard'
import { BookingPanel } from '../../features/bookings/booking-panel'
import { useDeleteRoom, useRoom, useUpdateRoom, type Room, type RoomInput } from '../../features/rooms/rooms'
import { toApiError } from '../../lib/api/errors'
import { Route as appRoute, Loading } from '../app'

export const Route = createRoute({
  getParentRoute: () => appRoute,
  path: '/rooms/$roomId',
  component: RoomDetailPage,
  pendingComponent: Loading,
})

function RoomDetailPage() {
  const { roomId } = Route.useParams()
  const { user } = Route.useRouteContext()
  const navigate = useNavigate()
  const { data: room, isPending, isError, error } = useRoom(roomId)

  if (isPending) return <p className="text-sm text-muted-foreground">Loading room…</p>
  if (isError) {
    return (
      <p role="alert" className="text-sm text-destructive">
        {error.message}
      </p>
    )
  }
  if (!room) return null

  return (
    <RoomView
      // remount whenever the server copy changes, so the form never drifts from it
      key={`${room.id}:${room.updated_at}`}
      room={room}
      canEdit={isAdmin(user)}
      onClose={() => navigate({ to: '/rooms' })}
    />
  )
}

function RoomView({
  room,
  canEdit,
  onClose,
}: {
  room: Room
  canEdit: boolean
  onClose: () => void
}) {
  const updateRoom = useUpdateRoom(room.id)
  const deleteRoom = useDeleteRoom()
  const [form, setForm] = useState<RoomInput>({
    name: room.name,
    location: room.location,
    capacity: room.capacity,
    description: room.description,
  })
  const [message, setMessage] = useState<string | null>(null)
  const busy = updateRoom.isPending || deleteRoom.isPending

  async function run(action: () => Promise<unknown>) {
    setMessage(null)
    try {
      await action()
    } catch (cause) {
      setMessage(toApiError(cause).message)
    }
  }

  async function onDelete() {
    if (!window.confirm(`Delete "${room.name}"? This cannot be undone.`)) return
    await deleteRoom.mutateAsync(room.id)
    onClose()
  }

  return (
    <>
      <Card className="max-w-lg">
        <CardHeader>
          <CardTitle>{room.name}</CardTitle>
          <CardDescription>
            {room.status === 'ACTIVE' ? 'Active' : 'Disabled'} · created{' '}
            {new Date(room.created_at).toLocaleDateString()}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {canEdit ? (
            <form
              className="flex flex-col gap-4"
              onSubmit={(event) => {
                event.preventDefault()
                void run(() => updateRoom.mutateAsync(form))
              }}
            >
              <Row id="name" label="Name">
                <Input
                  id="name"
                  required
                  maxLength={120}
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </Row>
              <Row id="location" label="Location">
                <Input
                  id="location"
                  required
                  maxLength={120}
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                />
              </Row>
              <Row id="capacity" label="Capacity">
                <Input
                  id="capacity"
                  type="number"
                  min={1}
                  max={500}
                  required
                  value={form.capacity}
                  onChange={(e) => setForm({ ...form, capacity: Number(e.target.value) })}
                />
              </Row>
              <Row id="description" label="Description">
                <Input
                  id="description"
                  maxLength={500}
                  value={form.description ?? ''}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </Row>
              {message && (
                <p role="alert" className="text-sm text-muted-foreground">
                  {message}
                </p>
              )}
              <div className="flex flex-wrap gap-2">
                <Button type="submit" disabled={busy}>
                  Save
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={busy}
                  onClick={() =>
                    void run(() =>
                      updateRoom.mutateAsync({
                        status: room.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE',
                      }),
                    )
                  }
                >
                  {room.status === 'ACTIVE' ? 'Disable' : 'Enable'}
                </Button>
                <Button type="button" variant="ghost" disabled={busy} onClick={onDelete}>
                  Delete
                </Button>
              </div>
            </form>
          ) : (
            <dl className="flex flex-col gap-2 text-sm">
              <Line term="Location" value={room.location} />
              <Line term="Capacity" value={String(room.capacity)} />
              <Line term="Description" value={room.description ?? '—'} />
            </dl>
          )}
        </CardContent>
      </Card>

      <p className="mt-4">
        <Button variant="ghost" size="sm" onClick={onClose}>
          ← All rooms
        </Button>
      </p>

      {!canEdit && room.status === 'ACTIVE' && <BookingPanel room={room} />}
    </>
  )
}

function Row({ id, label, children }: { id: string; label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
    </div>
  )
}

function Line({ term, value }: { term: string; value: string }) {
  return (
    <div className="flex gap-2">
      <dt className="w-28 shrink-0 text-muted-foreground">{term}</dt>
      <dd>{value}</dd>
    </div>
  )
}
