'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'

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

    if (!baseUrl.trim()) {
      newErrors.baseUrl = 'Base URL is required.'
    }
    if (!searchValues.trim()) {
      newErrors.searchValues = 'Search values are required.'
    }
    setErrors(newErrors)
    if (Object.keys(newErrors).length === 0) {
      // TODO: replace with submission logic
      console.log({
        baseUrl,
        searchValues: searchValues.split(',').map(v => v.trim()).filter(Boolean),
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
          <Input
            value={baseUrl}
            onChange={e => setBaseUrl(e.target.value)}
            placeholder="https://example.com"
          />
          {errors.baseUrl && <p className="mt-1 text-sm text-red-600">{errors.baseUrl}</p>}
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Search values</label>
          <Textarea
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
          <Switch checked={showAdvanced} onCheckedChange={setShowAdvanced} />
        </div>
        {showAdvanced && (
          <div className="space-y-4 border-l pl-4">
            <div>
              <label className="mb-1 block text-sm font-medium">Max pages</label>
              <Input
                type="number"
                min={1}
                value={maxPages}
                onChange={e => setMaxPages(parseInt(e.target.value) || 1)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Workers</label>
              <Input
                type="number"
                min={1}
                value={workers}
                onChange={e => setWorkers(parseInt(e.target.value) || 1)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Delay (seconds)</label>
              <Input
                type="number"
                min={0}
                step={0.1}
                value={delay}
                onChange={e => setDelay(parseFloat(e.target.value) || 0)}
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Respect robots.txt</span>
              <Switch checked={respectRobots} onCheckedChange={setRespectRobots} />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Track URL history</span>
              <Switch checked={trackHistory} onCheckedChange={setTrackHistory} />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Debug mode</span>
              <Switch checked={debugMode} onCheckedChange={setDebugMode} />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Export results</span>
              <Switch checked={exportResults} onCheckedChange={setExportResults} />
            </div>
          </div>
        )}
        <Button type="submit" className="w-full">
          Start Crawl
        </Button>
      </form>
    </div>
  )
}
