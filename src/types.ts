export type ChangeCategory = 'feature' | 'bugfix' | 'performance' | 'breaking' | 'other'
export type Impact = 'high' | 'medium' | 'low'

export interface Migration {
  required: boolean
  summary: string
  steps: string[]
}

export interface ReleaseChange {
  id: string
  category: ChangeCategory
  title: string
  summary: string
  impact: Impact
  breaking: boolean
}

export interface LibraryRelease {
  id: string
  library: string
  version: string
  publishedAt: string
  url: string
  breaking: boolean
  impact: Impact
  migration: Migration
  changes: ReleaseChange[]
}

export interface ReleaseFilters {
  dateRange: 'all' | '7d' | '30d' | '3m'
  libraries: string[]
  version: string
  breaking: 'all' | 'breaking' | 'non-breaking'
  impact: 'all' | Impact
}
