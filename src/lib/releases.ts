import type { LibraryRelease } from '../types'

const RELEASES_URL = '/data/releases.json'

export async function fetchReleases(): Promise<LibraryRelease[]> {
  const response = await fetch(RELEASES_URL)

  if (!response.ok) {
    throw new Error(`Release data could not be loaded: ${response.status}`)
  }

  return response.json() as Promise<LibraryRelease[]>
}
