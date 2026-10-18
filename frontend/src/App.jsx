// Application shell. Routing, providers, and pages are wired in later tasks;
// this placeholder confirms the dark theme tokens render correctly.
export default function App() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-8 text-center shadow-sm">
        <h1 className="text-2xl font-semibold tracking-tight text-card-foreground">
          Personal Blog
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Frontend scaffold running.
        </p>
      </div>
    </main>
  );
}
