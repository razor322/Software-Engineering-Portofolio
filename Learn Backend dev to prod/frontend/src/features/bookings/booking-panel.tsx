import { useState } from 'react'

import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { toApiError } from '../../lib/api/errors'
import { useAvailability, useCreateBooking } from './bookings'
import type { Room } from '../rooms/rooms'

/** `datetime-local` has no timezone; the API stores UTC, so convert on the way out. */
function toUtcIso(local: string): string {
  return new Date(local).toISOString()
}

function todayUtc(): string {
  return new Date().toISOString().slice(0, 10)
}

function clock(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function BookingPanel({ room }: { room: Room }) {
  const [day, setDay] = useState(todayUtc())
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [purpose, setPurpose] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const availability = useAvailability(room.id, day)
  const createBooking = useCreateBooking(room.id)

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault()
    setMessage(null)
    setError(null)
    try {
      await createBooking.mutateAsync({
        start_time: toUtcIso(start),
        end_time: toUtcIso(end),
        purpose: purpose || null,
      })
      setMessage('Booked.')
      setStart('')
      setEnd('')
      setPurpose('')
      setDay(start.slice(0, 10))
    } catch (cause) {
      setError(toApiError(cause).message)
    }
  }

  return (
    <div className="mt-6 grid gap-6 md:grid-cols-2">
      <section>
        <h2 className="text-sm font-semibold">Availability</h2>
        <div className="mt-2 flex flex-col gap-1.5">
          <Label htmlFor="day">Date (UTC)</Label>
          <Input
            id="day"
            type="date"
            value={day}
            onChange={(e) => setDay(e.target.value)}
          />
        </div>
        {availability.isPending && (
          <p className="mt-3 text-sm text-muted-foreground">Checking…</p>
        )}
        {availability.data && availability.data.length === 0 && (
          <p className="mt-3 text-sm text-muted-foreground">Free all day.</p>
        )}
        {availability.data && availability.data.length > 0 && (
          <ul className="mt-3 flex flex-col gap-1 text-sm">
            {availability.data.map((slot) => (
              <li key={slot.start_time} className="text-muted-foreground">
                {clock(slot.start_time)} – {clock(slot.end_time)} · {slot.status}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="text-sm font-semibold">Book this room</h2>
        <form className="mt-2 flex flex-col gap-3" onSubmit={onSubmit}>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="start">From</Label>
            <Input
              id="start"
              type="datetime-local"
              required
              value={start}
              onChange={(e) => setStart(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="end">To</Label>
            <Input
              id="end"
              type="datetime-local"
              required
              value={end}
              onChange={(e) => setEnd(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="purpose">Purpose (optional)</Label>
            <Input
              id="purpose"
              maxLength={255}
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
            />
          </div>
          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}
          {message && <p className="text-sm text-muted-foreground">{message}</p>}
          <Button type="submit" disabled={createBooking.isPending || !start || !end}>
            {createBooking.isPending ? 'Booking…' : 'Book'}
          </Button>
        </form>
      </section>
    </div>
  )
}
