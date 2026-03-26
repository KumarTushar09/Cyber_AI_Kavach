export function PromptInput({ value, onChange, onSubmit }: { value: string; onChange: (v: string) => void; onSubmit: () => void }) {
  return (
    <div className="grid" style={{ gridTemplateColumns: "1fr 120px" }}>
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder="Ask a security question" />
      <button onClick={onSubmit}>Send</button>
    </div>
  );
}
