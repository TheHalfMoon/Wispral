/*
 * Omalla Studio Browser Microphone AudioWorklet Processor.
 *
 * Captures mono Float32 microphone samples from Web Audio, resamples to 16 kHz,
 * emits exact 20 ms (320-sample / 640-byte) little-endian PCM16 frames, and
 * reports RMS energy for the live Studio waveform visualizer.
 */
class OmallaPcm16Worklet extends AudioWorkletProcessor {
  constructor() {
    super();
    this.targetRate = 16000;
    this.frameSamples = 320; // 20 ms @ 16 kHz
    this.buffer = new Int16Array(this.frameSamples);
    this.writeIndex = 0;
    this.resamplePhase = 0;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || input.length === 0) return true;
    const channel = input[0];
    if (!channel || channel.length === 0) return true;

    const inRate = typeof sampleRate === "number" && sampleRate > 0 ? sampleRate : 48000;
    const step = inRate / this.targetRate;

    let sumSq = 0;
    for (let i = 0; i < channel.length; i += 1) {
      const s = channel[i] || 0;
      sumSq += s * s;
    }
    const rms = Math.sqrt(sumSq / channel.length);

    while (this.resamplePhase < channel.length) {
      const idx = Math.floor(this.resamplePhase);
      const frac = this.resamplePhase - idx;
      const a = channel[idx] ?? 0;
      const b = channel[Math.min(channel.length - 1, idx + 1)] ?? a;
      const interpolated = a + (b - a) * frac;
      const clamped = Math.max(-1, Math.min(1, interpolated));
      this.buffer[this.writeIndex] = clamped < 0 ? Math.round(clamped * 32768) : Math.round(clamped * 32767);
      this.writeIndex += 1;

      if (this.writeIndex >= this.frameSamples) {
        const frameCopy = new Int16Array(this.buffer);
        this.port.postMessage(
          {
            type: "pcm16",
            rms,
            pcm16Buffer: frameCopy.buffer,
          },
          [frameCopy.buffer],
        );
        this.writeIndex = 0;
      }

      this.resamplePhase += step;
    }

    this.resamplePhase -= channel.length;
    return true;
  }
}

registerProcessor("omalla-pcm16-worklet", OmallaPcm16Worklet);
