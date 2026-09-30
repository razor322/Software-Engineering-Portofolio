import type { QueryClient } from '@tanstack/react-query'
import { Outlet, createRootRouteWithContext } from '@tanstack/react-router'

import { Button } from '../components/ui/button'

export type RouterContext = { queryClient: QueryClient }

export const Route = createRootRouteWithContext<RouterContext>()({
  component: () => <Outlet />,
  notFoundComponent: () => (
    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
      404 — page not found
    </div>
  ),
  // error boundary: every uncaught render or loader failure lands here instead of
  // blanking the page
  errorComponent: ({ error, reset }) => (
    <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
      <p className="text-sm font-medium">Something went wrong.</p>
      <p className="max-w-md text-sm text-muted-foreground">
        {error instanceof Error ? error.message : String(error)}
      </p>
      <Button onClick={reset}>Try again</Button>
    </div>
  ),
})
