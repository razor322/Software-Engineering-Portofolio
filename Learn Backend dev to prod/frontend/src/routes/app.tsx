import { Outlet, createRoute } from '@tanstack/react-router'

import { AppShell } from '../components/app-shell'
import { requireUser } from '../features/auth/guard'
import { Route as rootRoute } from './__root'

/**
 * Pathless layout for every signed-in page: resolves the session, then draws the
 * shell once instead of wrapping each route in it.
 */
export const Route = createRoute({
  getParentRoute: () => rootRoute,
  id: 'app',
  beforeLoad: requireUser,
  component: () => (
    <AppShell>
      <Outlet />
    </AppShell>
  ),
  pendingComponent: Loading,
})

export function Loading() {
  return (
    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
      Loading…
    </div>
  )
}
