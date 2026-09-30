import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { useLogin } from '../features/auth/session'
import { toApiError } from '../lib/api/errors'
import { createRoute } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: LoginPage,
})

function LoginPage() {
  const navigate = useNavigate()
  const login = useLogin()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      await login.mutateAsync({ email, password })
      await navigate({ to: '/dashboard' })
    } catch (cause) {
      setError(toApiError(cause).message)
    }
  }

  return (
    <div className="flex h-full items-center justify-center p-6">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Sign in to OfficeHub</CardTitle>
          <CardDescription>Use your company account.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-4" onSubmit={onSubmit}>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            {error && (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            )}
            <Button type="submit" disabled={login.isPending}>
              {login.isPending ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
