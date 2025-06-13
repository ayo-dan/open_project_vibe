'use client'

import { useState } from 'react'

export default function HomePage() {
  const [baseUrl, setBaseUrl] = useState('')
  const [searchValues, setSearchValues] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [maxPages, setMaxPages] = useState<number>(100)
  const [workers, setWorkers] = useState<number>(1)
  const [delay, setDelay] = useState<number>(2)
  const [respectRobots, setRespectRobots] = useState<boolean>(true)
  const [trackHistory, setTrackHistory] = useState<boolean>(false)
  const [debugMode, setDebugMode] = useState<boolean>(false)
  const [exportResults, setExportResults] = useState<boolean>(false)
  const [errors, setErrors] = useState<{ baseUrl?: string; searchValues?: string }>({})

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const newErrors: { baseUrl?: string; searchValues?: string } = {}
    if (!baseUrl.trim()) newErrors.baseUrl = 'Base URL is required.'
    if (!searchValues.trim()) newErrors.searchValues = 'Search values are required.'
    setErrors(newErrors)
    if (Object.keys(newErrors).length === 0) {
      console.log({
        baseUrl,
        searchValues: searchValues
          .split(',')
          .map(v => v.trim())
          .filter(Boolean),
        maxPages,
        workers,
        delay,
        respectRobots,
        trackHistory,
        debugMode,
        exportResults,
      })
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <form onSubmit={handleSubmit} className="w-full max-w-md space-y-6">
        <div>
          <label className="mb-1 block text-sm font-medium">Base URL</label>
          <input
            className="w-full rounded border px-2 py-1"
            value={baseUrl}
            onChange={e => setBaseUrl(e.target.value)}
            placeholder="https://example.com"
          />
          {errors.baseUrl && <p className="mt-1 text-sm text-red-600">{errors.baseUrl}</p>}
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Search values</label>
          <textarea
            className="w-full rounded border px-2 py-1"
            value={searchValues}
            onChange={e => setSearchValues(e.target.value)}
            placeholder="contact, form"
          />
          {errors.searchValues && (
            <p className="mt-1 text-sm text-red-600">{errors.searchValues}</p>
          )}
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Advanced settings</span>
          <input
            type="checkbox"
            checked={showAdvanced}
            onChange={e => setShowAdvanced(e.target.checked)}
            className="h-4 w-4"
          />
        </div>
        {showAdvanced && (
          <div className="space-y-4 border-l pl-4">
            <div>
              <label className="mb-1 block text-sm font-medium">Max pages</label>
              <input
                className="w-full rounded border px-2 py-1"
                type="number"
                min={1}
                value={maxPages}
                onChange={e => setMaxPages(parseInt(e.target.value) || 1)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Workers</label>
              <input
                className="w-full rounded border px-2 py-1"
                type="number"
                min={1}
                value={workers}
                onChange={e => setWorkers(parseInt(e.target.value) || 1)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Delay (seconds)</label>
              <input
                className="w-full rounded border px-2 py-1"
                type="number"
                min={0}
                step={0.1}
                value={delay}
                onChange={e => setDelay(parseFloat(e.target.value) || 0)}
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Respect robots.txt</span>
              <input
                type="checkbox"
                checked={respectRobots}
                onChange={e => setRespectRobots(e.target.checked)}
                className="h-4 w-4"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Track URL history</span>
              <input
                type="checkbox"
                checked={trackHistory}
                onChange={e => setTrackHistory(e.target.checked)}
                className="h-4 w-4"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Debug mode</span>
              <input
                type="checkbox"
                checked={debugMode}
                onChange={e => setDebugMode(e.target.checked)}
                className="h-4 w-4"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Export results</span>
              <input
                type="checkbox"
                checked={exportResults}
                onChange={e => setExportResults(e.target.checked)}
                className="h-4 w-4"
              />
            </div>
          </div>
        )}
        <button
          type="submit"
          className="w-full rounded bg-black px-4 py-2 text-white hover:bg-gray-800"
        >
          Start Crawl
        </button>
      </form>
    </div>
  )
}
