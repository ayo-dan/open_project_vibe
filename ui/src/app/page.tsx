import Link from "next/link";

export default function Home() {
  return (
    <main className="flex flex-col items-center justify-center gap-8 py-16 text-center font-sans">
      <h1 className="text-4xl font-bold tracking-tight">Where&apos;s My Value?</h1>
      <p className="max-w-prose text-lg text-muted-foreground">
        Use this interface to run the crawler and inspect results in your browser. The UI is under active
        development.
      </p>
      <p className="text-sm">
        Until then you can run
        <code className="mx-1 rounded bg-secondary px-1 py-0.5 font-mono">python wheres_my_value.py</code>
        from the command line.
      </p>
      <p className="text-sm">
        API documentation is available at <Link href="/docs" className="underline">/docs</Link>.
      </p>
    </main>
  );
}
