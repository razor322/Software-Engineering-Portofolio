import { createRouter } from '@tanstack/react-router'

import { Route as appRoute } from './routes/app'
import { Route as bookingsRoute } from './routes/bookings'
import { Route as dashboardRoute } from './routes/dashboard'
import { Route as indexRoute } from './routes/index'
import { Route as loginRoute } from './routes/login'
import { Route as roomNewRoute } from './routes/rooms/new'
import { Route as roomDetailRoute } from './routes/rooms/$roomId'
import { Route as roomsRoute } from './routes/rooms'
import { Route as rootRoute } from './routes/__root'

export const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  appRoute.addChildren([
    dashboardRoute,
    roomsRoute,
    roomNewRoute,
    roomDetailRoute,
    bookingsRoute,
  ]),
])

export function createAppRouter(context: { queryClient: import('@tanstack/react-query').QueryClient }) {
  return createRouter({
    routeTree,
    context,
    defaultPreload: 'intent',
  })
}

declare module '@tanstack/react-router' {
  interface Register {
    router: ReturnType<typeof createAppRouter>
  }
}
