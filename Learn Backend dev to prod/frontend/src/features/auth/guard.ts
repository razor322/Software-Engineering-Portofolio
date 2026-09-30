import type { QueryClient } from '@tanstack/react-query'
import { redirect } from '@tanstack/react-router'

import { sessionQuery, type SessionUser } from './session'

export type SessionContext = { context: { queryClient: QueryClient } }

/**
 * The single guard every authenticated route reuses: resolve the session once,
 * bounce anonymous visitors to /login before any page renders.
 */
export async function requireUser({ context }: SessionContext): Promise<{ user: SessionUser }> {
  const user = await context.queryClient.ensureQueryData(sessionQuery)
  if (!user) throw redirect({ to: '/login' })
  return { user }
}

/**
 * UI visibility only — the backend re-checks every permission on every request.
 * Role names are duplicated here on purpose; nothing security-relevant depends on it.
 */
export function isAdmin(user: SessionUser | null | undefined): boolean {
  return user?.roles.includes('ADMIN') ?? false
}
