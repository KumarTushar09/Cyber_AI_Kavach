export function MessageBubble({ role, text }: { role: "user" | "assistant"; text: string }) {
  const background = role === "user" ? "#e0f2fe" : "#dcfce7";
  return <div style={{ background, padding: 10, borderRadius: 10, marginBottom: 8 }}>{text}</div>;
}
