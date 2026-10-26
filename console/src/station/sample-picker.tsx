import { useEffect, useState } from "react";

type Sample = { id: string; kind: "legit" | "attack"; category: string; note: string };

type Props = { onPick: (id: string) => void; isDisabled: boolean };

export const SamplePicker = ({ onPick, isDisabled }: Props) => {
  const [samples, setSamples] = useState<Sample[]>([]);
  const [chosen, setChosen] = useState("");

  useEffect(() => {
    void fetch("/api/samples").then(async (r) => r.ok && setSamples(await r.json()));
  }, []);

  if (samples.length === 0) return null;
  return (
    <form className="picker" onSubmit={(e) => { e.preventDefault(); if (chosen) onPick(chosen); }}>
      <select className="mono" value={chosen} onChange={(e) => setChosen(e.target.value)}>
        <option value="">recorded frame...</option>
        {samples.map((s) => (
          <option key={s.id} value={s.id}>{s.id} {s.kind} {s.category}{s.note ? `: ${s.note.slice(0, 48)}` : ""}</option>
        ))}
      </select>
      <button type="submit" disabled={isDisabled || !chosen}>Run frame</button>
    </form>
  );
};
