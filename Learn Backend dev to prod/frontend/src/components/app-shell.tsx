import { Link, useRouterState } from '@tanstack/react-router'

import { useLogout, useSession } from '../features/auth/session'
import { Button } from './ui/button'
import { cn } from '../lib/utils'

// ponytail: Dashboard, Rooms, and Bookings exist (Phases 02, 05, 06). The rest are
// rendered inert rather than as links to routes that do not exist.
const NAV = [
  { to: '/dashboard', label: 'Dashboard', ready: true },
  { to: '/rooms', label: 'Rooms', ready: true },
  { to: '/bookings', label: 'Bookings', ready: true },
  { to: '/tickets', label: 'Tickets', ready: false },
] as const

export function AppShell({ children }: { children: React.ReactNode }) {
  const { data: user } = useSession()
  const logout = useLogout()
  const router = useRouterState()
  const activePath = router.location.pathname

  return (
    <div className="flex h-full">
      <aside className="flex w-60 shrink-0 flex-col border-r border-border bg-muted">
        <div className="px-5 py-4 text-sm font-semibold">OfficeHub</div>
        <nav className="flex flex-col gap-1 px-3">
          {NAV.map((item) =>
            item.ready ? (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  'rounded-md px-3 py-2 text-sm',
                  activePath.startsWith(item.to)
                    ? 'bg-background font-medium text-foreground'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {item.label}
              </Link>
            ) : (
              <span
                key={item.to}
                aria-disabled
                className="flex cursor-not-allowed items-center justify-between rounded-md px-3 py-2 text-sm text-muted-foreground/60"
              >
                {item.label}
                <span className="text-[10px] uppercase tracking-wide">soon</span>
              </span>
            ),
          )}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-end gap-3 border-b border-border px-6">
          <span className="text-sm text-muted-foreground">
            {user ? `${user.name} · ${user.roles.join(', ')}` : ''}
          </span>
          <Button variant="outline" size="sm" onClick={() => logout.mutate()} disabled={logout.isPending}>
            Sign out
          </Button>
        </header>
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  )
}
