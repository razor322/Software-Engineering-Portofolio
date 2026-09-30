import axios from 'axios'

/**
 * The backend answers every failure with the same envelope (PRD 4.2), so the UI
 * can render one consistent error state instead of guessing per endpoint.
 */
export type ApiErrorEnvelope = {
  error: {
    code: string
    message: string
    request_id?: string
    details?: { loc?: (string | number)[]; msg?: string; type?: string }[]
  }
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly requestId?: string

  constructor(status: number, envelope: ApiErrorEnvelope | null) {
    super(envelope?.error.message ?? 'Request failed.')
    this.name = 'ApiError'
    this.status = status
    this.code = envelope?.error.code ?? 'UNKNOWN'
    this.requestId = envelope?.error.request_id
  }

  get isUnauthorized() {
    return this.status === 401
  }
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error
  if (axios.isAxiosError(error)) {
    return new ApiError(error.response?.status ?? 0, (error.response?.data ?? null) as ApiErrorEnvelope | null)
  }
  return new ApiError(0, null)
}
