function format(value) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return value.toLocaleString("en-IN");
  return String(value);
}

export default function ResultsTable({ columns, rows, truncated }) {
  if (rows.length === 0) {
    return <p className="text-gray-500 text-sm">The query ran but returned no rows.</p>;
  }
  return (
    <div>
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-sm text-left">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              {columns.map((c) => (
                <th key={c} className="px-4 py-2 font-medium whitespace-nowrap">{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className="border-t">
                {columns.map((c) => (
                  <td key={c} className="px-4 py-2 whitespace-nowrap">{format(row[c])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {truncated && (
        <p className="mt-2 text-xs text-amber-700">
          Results were cut off at 100 rows. Add a filter to narrow the question.
        </p>
      )}
    </div>
  );
}