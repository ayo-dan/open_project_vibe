"use client";
import { FormEvent, useState } from "react";
import Link from "next/link";

interface CrawlSummary {
  found_values: string[];
  pages_visited: number;
  errors: number;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "/.netlify/functions/api";

async function fetchSummary(
  baseUrl: string,
  searchValues: string[],
): Promise<CrawlSummary> {
  const response = await fetch(`${API_BASE_URL}/crawl-summary`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ base_url: baseUrl, search_values: searchValues, max_pages: 5 }),
  });

  if (!response.ok) {
    throw new Error("Request failed");
  }
  return response.json();
}

export default function Home() {
  const [baseUrl, setBaseUrl] = useState("");
  const [searchValues, setSearchValues] = useState("");
  const [summary, setSummary] = useState<CrawlSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSummary(null);
    setError(null);
    try {
      setIsLoading(true);
      const result = await fetchSummary(
        baseUrl.trim(),
        searchValues.split(",").map((v) => v.trim()).filter(Boolean),
      );
      setSummary(result);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="container mx-auto max-w-xl space-y-6 py-12 font-sans">
      <h1 className="text-center text-4xl font-bold tracking-tight">Where&apos;s My Value?</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="base-url" className="mb-1 block font-medium">
            Base URL
          </label>
          <input
            id="base-url"
            type="text"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            className="w-full rounded border px-2 py-1"
            required
          />
        </div>

        <div>
          <label htmlFor="search-values" className="mb-1 block font-medium">
            Search values
          </label>
          <input
            id="search-values"
            type="text"
            value={searchValues}
            onChange={(e) => setSearchValues(e.target.value)}
            className="w-full rounded border px-2 py-1"
            placeholder="comma,separated,values"
            required
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50"
        >
          {isLoading ? "Crawling..." : "Crawl"}
        </button>
      </form>

      {error && <p className="text-destructive">{error}</p>}
      {summary && (
        <div className="rounded border p-4">
          <p>
            <span className="font-medium">Pages visited:</span> {summary.pages_visited}
          </p>
          <p>
            <span className="font-medium">Errors:</span> {summary.errors}
          </p>
          <p>
            <span className="font-medium">Found values:</span> {summary.found_values.join(", ") || "None"}
          </p>
        </div>
      )}

      <p className="text-center text-sm">
        API documentation is available at <Link href="/docs" className="underline">/docs</Link>.
      </p>
    </main>
  );
}
