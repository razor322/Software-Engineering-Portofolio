import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'

import { Button } from '../../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { useCreateRoom } from '../../features/rooms/rooms'
import { toApiError } from '../../lib/api/errors'
import { createRoute, redirect } from '@tanstack/react-router'
import { Route as appRoute } from '../app'

export const Route = createRoute({
  getParentRoute: () => appRoute,
  path: '/rooms/new',
  // the form is for admins only; the API would reject anyone else anyway
  beforeLoad: ({ context }) => {
    if (!context.user.roles.includes('ADMIN')) {
      throw redirect({ to: '/rooms' })
    }
  },
  component: NewRoomPage,
})

function NewRoomPage() {
  const navigate = useNavigate()
  const createRoom = useCreateRoom()
  const [form, setForm] = useState({ name: '', location: '', capacity: '', description: '' })
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      const room = await createRoom.mutateAsync({
        name: form.name,
        location: form.location,
        capacity: Number(form.capacity),
        description: form.description || null,
      })
      await navigate({ to: '/rooms/$roomId', params: { roomId: room.id } })
    } catch (cause) {
      setError(toApiError(cause).message)
    }
  }

  return (
    <Card className="max-w-lg">
      <CardHeader>
        <CardTitle>New room</CardTitle>
        <CardDescription>A room employees can see and book.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="flex flex-col gap-4" onSubmit={onSubmit}>
          <Field id="name" label="Name">
            <Input
              id="name"
              required
              maxLength={120}
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </Field>
          <Field id="location" label="Location">
            <Input
              id="location"
              required
              maxLength={120}
              value={form.location}
              onChange={(e) => setForm({ ...form, location: e.target.value })}
            />
          </Field>
          <Field id="capacity" label="Capacity">
            <Input
              id="capacity"
              type="number"
              min={1}
              max={500}
              required
              value={form.capacity}
              onChange={(e) => setForm({ ...form, capacity: e.target.value })}
            />
          </Field>
          <Field id="description" label="Description (optional)">
            <Input
              id="description"
              maxLength={500}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </Field>
          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}
          <div className="flex gap-2">
            <Button type="submit" disabled={createRoom.isPending}>
              {createRoom.isPending ? 'Creating…' : 'Create room'}
            </Button>
            <Button type="button" variant="outline" onClick={() => navigate({ to: '/rooms' })}>
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

function Field({
  id,
  label,
  children,
}: {
  id: string
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
    </div>
  )
}
