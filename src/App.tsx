import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { flexRender, getCoreRowModel, useReactTable, type ColumnDef } from '@tanstack/react-table'
import { fetchReleases } from './lib/releases'
import type { Impact, LibraryRelease, ReleaseFilters } from './types'

const initialFilters: ReleaseFilters = { dateRange: '30d', exactDate: '', libraries: [], version: '', breaking: 'all', impact: 'all' }
const categoryLabels: Record<string, string> = { feature: 'Feature', bugfix: 'Bug Fix', performance: 'Performance', breaking: 'Breaking Change', other: 'Other' }
const impactLabels: Record<Impact, string> = { high: 'High', medium: 'Medium', low: 'Low' }

function isWithinRange(date: string, range: ReleaseFilters['dateRange']) {
  if (range === 'all') return true
  const days = range === '7d' ? 7 : range === '30d' ? 30 : 90
  return new Date(date).getTime() >= Date.now() - days * 24 * 60 * 60 * 1000
}
function formatDate(value: string) { return new Intl.DateTimeFormat('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit', timeZone: 'Asia/Tokyo' }).format(new Date(value)) }
function getJapanDate(value: string) { return new Intl.DateTimeFormat('en-CA', { year: 'numeric', month: '2-digit', day: '2-digit', timeZone: 'Asia/Tokyo' }).format(new Date(value)) }

function App() {
  const [filters, setFilters] = useState(initialFilters)
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const releasesQuery = useQuery({ queryKey: ['releases'], queryFn: fetchReleases })
  const releases = releasesQuery.data ?? []
  const libraries = useMemo(() => [...new Set(releases.map((release) => release.library))].sort(), [releases])

  const filteredReleases = useMemo(() => releases
    .filter((release) => isWithinRange(release.publishedAt, filters.dateRange))
    .filter((release) => !filters.exactDate || getJapanDate(release.publishedAt) === filters.exactDate)
    .filter((release) => filters.libraries.length === 0 || filters.libraries.includes(release.library))
    .filter((release) => release.version.toLowerCase().includes(filters.version.toLowerCase()))
    .filter((release) => filters.breaking === 'all' || (filters.breaking === 'breaking' ? release.breaking : !release.breaking))
    .filter((release) => filters.impact === 'all' || release.impact === filters.impact)
    .sort((a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime()), [releases, filters])

  const columns = useMemo<ColumnDef<LibraryRelease>[]>(() => [
    { accessorKey: 'library', header: 'Library' },
    { accessorKey: 'version', header: 'Version' },
    { accessorKey: 'publishedAt', header: 'Date', cell: ({ getValue }) => formatDate(getValue<string>()) },
    { accessorKey: 'impact', header: 'Impact', cell: ({ getValue }) => <span className={`badge impact-${getValue<string>()}`}>{impactLabels[getValue<Impact>()]}</span> },
    { accessorKey: 'breaking', header: 'Status', cell: ({ row }) => <div className="status-badges">{row.original.breaking && <span className="badge badge-breaking">Breaking</span>}{row.original.migration.required && <span className="badge badge-migration">Migration</span>}{!row.original.breaking && !row.original.migration.required && <span className="badge badge-neutral">Normal</span>}</div> },
  ], [])
  const table = useReactTable({ data: filteredReleases, columns, getCoreRowModel: getCoreRowModel() })
  const toggleLibrary = (library: string) => setFilters((current) => ({ ...current, libraries: current.libraries.includes(library) ? current.libraries.filter((item) => item !== library) : [...current.libraries, library] }))
  const setFilter = <K extends keyof ReleaseFilters>(key: K, value: ReleaseFilters[K]) => setFilters((current) => ({ ...current, [key]: value }))

  if (releasesQuery.isPending) return <main className="state">Releaseを読み込んでいます...</main>
  if (releasesQuery.isError) return <main className="state error">Releaseの読み込みに失敗しました。</main>

  return <main className="app-shell">
    <header className="hero"><div><p className="eyebrow">LIBRARY RELEASE TRACKER</p><h1>Library Release Tracker</h1><p>Release Notesを「自分が判断しやすい情報」に変換して蓄積する。</p></div><div className="summary-card"><strong>{filteredReleases.length}</strong><span>releases</span></div></header>
    <section className="filters" aria-label="Release filters">
      <label>Date range<select value={filters.dateRange} onChange={(event) => setFilter('dateRange', event.target.value as ReleaseFilters['dateRange'])}><option value="all">All</option><option value="7d">Last 7 days</option><option value="30d">Last 30 days</option><option value="3m">Last 3 months</option></select></label>
      <label>Exact date<input type="date" value={filters.exactDate} onChange={(event) => setFilter('exactDate', event.target.value)} /></label>
      <label>Version<input value={filters.version} onChange={(event) => setFilter('version', event.target.value)} placeholder="19.2.0" /></label>
      <label>Breaking<select value={filters.breaking} onChange={(event) => setFilter('breaking', event.target.value as ReleaseFilters['breaking'])}><option value="all">All</option><option value="breaking">Breaking only</option><option value="non-breaking">No breaking</option></select></label>
      <label>Impact<select value={filters.impact} onChange={(event) => setFilter('impact', event.target.value as ReleaseFilters['impact'])}><option value="all">All</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></label>
      <div className="library-filter"><span>Library</span><div className="library-options">{libraries.map((library) => <label className="checkbox" key={library}><input type="checkbox" checked={filters.libraries.includes(library)} onChange={() => toggleLibrary(library)} />{library}</label>)}</div></div>
    </section>
    <section className="release-list" aria-label="Release list"><table><thead>{table.getHeaderGroups().map((headerGroup) => <tr key={headerGroup.id}>{headerGroup.headers.map((header) => <th key={header.id}>{flexRender(header.column.columnDef.header, header.getContext())}</th>)}<th>Changes</th></tr>)}</thead>
      <tbody>{table.getRowModel().rows.map((row) => { const release = row.original; const isExpanded = expanded[release.id] ?? false; return <tr key={row.id} className={isExpanded ? 'expanded-row' : undefined}>
        {row.getVisibleCells().map((cell) => <td key={cell.id} data-label={String(cell.column.columnDef.header)}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}
        <td><button className="expand-button" onClick={() => setExpanded((current) => ({ ...current, [release.id]: !isExpanded }))}>{isExpanded ? '▲ Close' : `▼ ${release.changes.length} changes`}</button>{isExpanded && <div className="details"><div className="detail-heading"><div><h2>{release.library} {release.version}</h2><p>{release.migration.required ? release.migration.summary : 'Migrationは不要です。'}</p></div><a href={release.url} target="_blank" rel="noreferrer">GitHub Release ↗</a></div>{release.migration.required && <div className="migration-box"><strong>🔄 Migration Required</strong><ol>{release.migration.steps.map((step) => <li key={step}>{step}</li>)}</ol></div>}<div className="changes">{release.changes.map((change) => <details key={change.id} className="change-item"><summary><span>{change.title}</span><span className="change-meta"><span>{categoryLabels[change.category]}</span><span className={`badge impact-${change.impact}`}>{impactLabels[change.impact]}</span>{change.breaking && <span className="badge badge-breaking">Breaking</span>}</span></summary><p>{change.summary}</p></details>)}</div></div>}</td>
      </tr> })}{table.getRowModel().rows.length === 0 && <tr><td colSpan={6} className="empty">条件に一致するReleaseがありません。</td></tr>}</tbody></table></section>
  </main>
}
export default App
