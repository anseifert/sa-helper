const colors: Record<string, string> = {
  gmail: "bg-blue-100 text-blue-800",
  calendar: "bg-green-100 text-green-800",
  drive: "bg-yellow-100 text-yellow-800",
  slack: "bg-purple-100 text-purple-800",
};

export default function Badge({ source }: { source: string }) {
  return (
    <span
      className={`text-xs px-2 py-0.5 rounded font-medium uppercase ${
        colors[source] || "bg-gray-100 text-gray-700"
      }`}
    >
      {source}
    </span>
  );
}
