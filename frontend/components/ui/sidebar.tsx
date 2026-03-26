export function Sidebar() {
  return (
    <div
      className="card"
      style={{
        background: "#ffffff",
        color: "#10151f",
        border: "1px solid #dce3ee",
        borderRadius: 14,
        padding: 16,
        marginBottom: 16,
        boxShadow: "0 8px 24px rgba(16, 21, 31, 0.06)",
      }}
    >
      <p><a href="/" style={{ color: "#0f766e" }}>Home</a></p>
      <p><a href="/fraud-check" style={{ color: "#0f766e" }}>Fraud Check</a></p>
      <p><a href="/knowledge-assistant" style={{ color: "#0f766e" }}>Knowledge Assistant</a></p>
      <p><a href="/upload" style={{ color: "#0f766e" }}>Upload</a></p>
    </div>
  );
}
