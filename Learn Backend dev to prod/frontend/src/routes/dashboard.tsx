import { createRoute } from '@tanstack/react-router'

import { Route as appRoute } from './app'

export const Route = createRoute({
  getParentRoute: () => appRoute,
  path: '/dashboard',
  component: Dashboard,
})

function Dashboard() {
  const { user } = Route.useRouteContext()

  return (
    <>
      <h1 className="text-xl font-semibold">Dashboard</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Signed in as {user.name} ({user.email}).
      </p>
      <p className="mt-6 max-w-prose text-sm text-muted-foreground">
        Bookings and ticketing arrive in Phases 06–07; the sidebar already marks them.
      </p>
    </>
  )
}
