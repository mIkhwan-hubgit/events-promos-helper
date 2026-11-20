// The little rewards: confetti and a soft "pop" sound
import confetti from "canvas-confetti";

export type Origin = { x: number; y: number }; // 0 to 1 across and down the screen

// Where an element sits on the screen, so confetti can burst from it
export function originOf(element: Element | null): Origin | undefined {
  if (!element) return undefined;
  const box = element.getBoundingClientRect();
  return { x: (box.left + box.width / 2) / window.innerWidth, y: (box.top + box.height / 2) / window.innerHeight };
}

export function celebrate(origin?: Origin) {
  // use the site's own tab colours
  const styles = getComputedStyle(document.documentElement);
  const colors = ["--books", "--tech", "--orchestra", "--workshop", "--games", "--sticker"]
    .map((name) => styles.getPropertyValue(name).trim())
    .filter(Boolean);
  confetti({
    particleCount: 90,
    spread: 75,
    startVelocity: 38,
    origin: origin ?? { x: 0.5, y: 0.7 },
    colors,
    zIndex: 100,
    disableForReducedMotion: true, // no confetti for visitors who turned off animations
  });
}

let audio: AudioContext | null = null;

// Plays a short tone made in the browser (no sound files needed)
function tone(context: AudioContext, start: number, from: number, to: number) {
  const oscillator = context.createOscillator();
  const volume = context.createGain();
  oscillator.type = "sine";
  oscillator.frequency.setValueAtTime(from, start);
  oscillator.frequency.exponentialRampToValueAtTime(to, start + 0.09);
  volume.gain.setValueAtTime(0.0001, start);
  volume.gain.exponentialRampToValueAtTime(0.2, start + 0.01);
  volume.gain.exponentialRampToValueAtTime(0.0001, start + 0.2);
  oscillator.connect(volume).connect(context.destination);
  oscillator.start(start);
  oscillator.stop(start + 0.22);
}

export function playSound(kind: "want" | "going" | "remove") {
  try {
    audio ??= new AudioContext();
    const now = audio.currentTime;
    if (kind === "remove") tone(audio, now, 520, 260);
    else if (kind === "want") tone(audio, now, 440, 880);
    else {
      tone(audio, now, 523, 1046); // two happy notes for "Going"
      tone(audio, now + 0.12, 784, 1568);
    }
  } catch {
    // some browsers block sound; it's only a bonus
  }
}