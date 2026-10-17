import { useState } from "react";
import { ask } from "./api";
import ResultsTable from "./components/ResultsTable";

const EXAMPLES = [
  "Top 3 customers by total revenue",
  "How many orders are pending?",
  "Total revenue per product category",
  "Which customers live in Chennai?",
  "Monthly revenue for 2026",
];

export default function App() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [explain, setExplain] = useState(true);
  const [copied, setCopied] = useState(false);

  async function run(q) {
    const text = (q ?? question).trim();
    if (text.length < 3) {
      setError("Please type a question (at least 3 characters).");
      return;
    }
    setQuestion(text);
    setError("");
    setResult(null);
    setLoading(true);
    try {
      setResult(await ask(text, explain));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function copySql() {
    try {
      await navigator.clipboard.writeText(result.sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard can be blocked; ignore */
    }
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">AskDB</h1>
          <p className="text-sm text-gray-500">
            Ask questions about the shop database in plain English.
          </p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-4 space-y-4">
        <form
          onSubmit={(e) => { e.preventDefault(); run(); }}
          className="bg-white rounded-xl shadow p-4 space-y-3"
        >
          <textarea
            className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            rows="3" maxLength={500}
            placeholder="e.g. Top 3 customers by total revenue"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />

          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button type="button" key={ex} disabled={loading}
                      onClick={() => run(ex)}
                      className="rounded-full border border-gray-300 px-3 py-1 text-xs text-gray-700 hover:bg-gray-100 disabled:opacity-50">
                {ex}
              </button>
            ))}
          </div>

          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input type="checkbox" checked={explain} onChange={(e) => setExplain(e.target.checked)} />
              Explain in plain English
            </label>
            <button disabled={loading}
                    className="rounded-lg bg-indigo-600 text-white px-4 py-2 font-medium hover:bg-indigo-700 disabled:opacity-50">
              {loading ? "Thinking..." : "Ask"}
            </button>
          </div>
        </form>

        {error && (
          <div className="rounded-lg bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>
        )}

        {result && (
          <div className="bg-white rounded-xl shadow p-4 space-y-4">
            {result.explanation && (
              <p className="text-gray-800">{result.explanation}</p>
            )}

            <div>
              <div className="flex items-center justify-between mb-1">
                <h2 className="text-sm font-semibold text-gray-600">Generated SQL</h2>
                <button onClick={copySql} className="text-xs text-indigo-600 hover:underline">
                  {copied ? "Copied" : "Copy"}
                </button>
              </div>
              <pre className="bg-gray-900 text-green-300 text-sm rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">
                {result.sql}
              </pre>
            </div>

            <div>
              <h2 className="text-sm font-semibold text-gray-600 mb-1">
                Results ({result.row_count} {result.row_count === 1 ? "row" : "rows"})
              </h2>
              <ResultsTable columns={result.columns} rows={result.rows} truncated={result.truncated} />
            </div>

            {result.attempts > 1 && (
              <p className="text-xs text-gray-500">
                The first query failed validation, so the model corrected it (attempt {result.attempts}).
              </p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}