import { type FormEvent, useState } from "react";

const JURISDICTIONS = [
  { id: "00000000-0000-0000-0000-000000000401", label: "United Kingdom" },
  { id: "00000000-0000-0000-0000-000000000402", label: "United States" }
];

export type QueryFormProps = {
  onSubmit: (text: string, jurisdictionId: string) => void;
  disabled: boolean;
};

export function QueryForm({ onSubmit, disabled }: QueryFormProps) {
  const [text, setText] = useState("");
  const [jurisdictionId, setJurisdictionId] = useState(JURISDICTIONS[0].id);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = text.trim();
    if (trimmed.length === 0) {
      return;
    }
    onSubmit(trimmed, jurisdictionId);
  }

  return (
    <form onSubmit={handleSubmit} className="query-form">
      <label htmlFor="jurisdiction">Jurisdiction</label>
      <select
        id="jurisdiction"
        value={jurisdictionId}
        onChange={(event) => setJurisdictionId(event.target.value)}
        disabled={disabled}
      >
        {JURISDICTIONS.map((jurisdiction) => (
          <option key={jurisdiction.id} value={jurisdiction.id}>
            {jurisdiction.label}
          </option>
        ))}
      </select>

      <label htmlFor="query-text">Your question</label>
      <textarea
        id="query-text"
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="e.g. How do I treat varroa mites in autumn?"
        rows={3}
        disabled={disabled}
      />

      <button type="submit" disabled={disabled || text.trim().length === 0}>
        {disabled ? "Asking..." : "Ask"}
      </button>
    </form>
  );
}
