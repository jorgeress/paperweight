import type { Outcome } from "../decision/types";

type Beep = { hz: number; ms: number; gapMs: number };

const PATTERNS: Record<Outcome, Beep[]> = {
  allow: [{ hz: 1320, ms: 110, gapMs: 0 }],
  hold: [
    { hz: 660, ms: 150, gapMs: 90 },
    { hz: 660, ms: 150, gapMs: 0 },
  ],
  deny: [{ hz: 180, ms: 650, gapMs: 0 }],
};

let context: AudioContext | null = null;

// note: browsers keep audio muted until a user gesture, so the first click anywhere unlocks it
export const unlockBuzzer = () => {
  context ??= new AudioContext();
  void context.resume();
};

export const soundVerdict = (outcome: Outcome) => {
  if (!context || context.state !== "running") return;
  let at = context.currentTime;
  for (const beep of PATTERNS[outcome]) {
    const tone = context.createOscillator();
    const gain = context.createGain();
    tone.type = "square";
    tone.frequency.value = beep.hz;
    gain.gain.setValueAtTime(0.08, at);
    gain.gain.setValueAtTime(0, at + beep.ms / 1000);
    tone.connect(gain).connect(context.destination);
    tone.start(at);
    tone.stop(at + beep.ms / 1000);
    at += (beep.ms + beep.gapMs) / 1000;
  }
};
