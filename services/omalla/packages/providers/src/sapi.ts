import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { OmallaError } from "@omalla/core";
import type {
  SttOptions,
  SttProvider,
  SynthesizedAudio,
  TranscriptResult,
  TtsOptions,
  TtsProvider,
} from "@omalla/core";
import { wavDurationMs } from "@omalla/core";

const VOICE_ALIASES: Record<string, string> = {
  zira: "Microsoft Zira Desktop",
  david: "Microsoft David Desktop",
  mark: "Microsoft Mark",
  "zira-desktop": "Microsoft Zira Desktop",
  "david-desktop": "Microsoft David Desktop",
};

const TTS_SCRIPT = `
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$text = [Console]::In.ReadToEnd()
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
if ($env:OMALLA_VOICE) { $synth.SelectVoice($env:OMALLA_VOICE) }
$synth.Rate = [int]$env:OMALLA_RATE
$synth.SetOutputToWaveFile($env:OMALLA_OUT)
$synth.Speak($text)
$synth.Dispose()
`;

const STT_SCRIPT = `
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$culture = New-Object System.Globalization.CultureInfo($env:OMALLA_LANG)
$engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine($culture)
$engine.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
$engine.SetInputToWaveFile($env:OMALLA_IN)
$result = $engine.Recognize()
if ($null -ne $result) { [Console]::Out.Write($result.Text) }
$engine.Dispose()
`;

/**
 * Windows SAPI text-to-speech.
 *
 * This is the honest zero-cost local voice path on this machine: offline,
 * no account, no model download. Arabic is not installed by default, so the
 * registry only offers this provider for languages SAPI can voice.
 */
export class SapiTts implements TtsProvider {
  readonly id = "sapi";
  private readonly cache = new Map<string, SynthesizedAudio>();
  private readonly maxCache = 64;

  async synthesize(text: string, options: TtsOptions): Promise<SynthesizedAudio> {
    assertWindows();
    if (options.signal?.aborted) throw abortError();

    const voice = resolveVoice(options.voiceId);
    const rate = speedToRate(options.speed ?? 1);
    const key = createHash("sha256").update(`${text}|${voice}|${rate}`).digest("hex");
    const cached = this.cache.get(key);
    if (cached) return cached;

    const dir = await mkdtemp(path.join(tmpdir(), "omalla-tts-"));
    const outPath = path.join(dir, "out.wav");
    try {
      const result = await runPowerShell(TTS_SCRIPT, {
        stdin: text,
        env: { OMALLA_VOICE: voice, OMALLA_RATE: String(rate), OMALLA_OUT: outPath },
        timeoutMs: 30_000,
      });
      if (result.code !== 0) {
        throw new OmallaError("provider_error", `SAPI TTS failed: ${result.stderr.slice(0, 200)}`, 502);
      }
      const data = new Uint8Array(await readFile(outPath));
      const audio: SynthesizedAudio = {
        data,
        mimeType: "audio/wav",
        durationMs: wavDurationMs(data),
      };
      if (this.cache.size >= this.maxCache) {
        const first = this.cache.keys().next().value;
        if (first) this.cache.delete(first);
      }
      this.cache.set(key, audio);
      return audio;
    } finally {
      await rm(dir, { recursive: true, force: true }).catch(() => {});
    }
  }
}

/**
 * Windows SAPI dictation. Offline and free; accuracy is below modern neural
 * models, so the product surfaces it as a development provider rather than a
 * production transcription claim.
 */
export class SapiStt implements SttProvider {
  readonly id = "sapi";
  private readonly languages = new Set(["en-US", "fr-FR", "zh-CN", "zh-TW"]);

  async transcribe(audio: Uint8Array, options: SttOptions = {}): Promise<TranscriptResult> {
    assertWindows();
    const language = options.language && this.languages.has(options.language) ? options.language : "en-US";
    const dir = await mkdtemp(path.join(tmpdir(), "omalla-stt-"));
    const inPath = path.join(dir, "in.wav");
    try {
      await writeFile(inPath, audio);
      const result = await runPowerShell(STT_SCRIPT, {
        env: { OMALLA_IN: inPath, OMALLA_LANG: language },
        timeoutMs: 30_000,
      });
      if (result.code !== 0) {
        throw new OmallaError("provider_error", `SAPI STT failed: ${result.stderr.slice(0, 200)}`, 502);
      }
      const text = result.stdout.trim();
      return { text, confidence: text ? 0.6 : 0, isFinal: true, language };
    } finally {
      await rm(dir, { recursive: true, force: true }).catch(() => {});
    }
  }
}

export async function sapiAvailable(): Promise<boolean> {
  if (process.platform !== "win32") return false;
  try {
    const result = await runPowerShell(
      "Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; [Console]::Out.Write($s.GetInstalledVoices().Count); $s.Dispose()",
      { timeoutMs: 15_000 },
    );
    return result.code === 0 && Number(result.stdout.trim()) > 0;
  } catch {
    return false;
  }
}

function resolveVoice(voiceId: string): string {
  const key = voiceId.toLowerCase().trim();
  return VOICE_ALIASES[key] ?? voiceId;
}

function speedToRate(speed: number): number {
  // SAPI rate is -10..10; 1.0 maps to normal delivery.
  return Math.max(-10, Math.min(10, Math.round((speed - 1) * 10)));
}

function assertWindows(): void {
  if (process.platform !== "win32") {
    throw new OmallaError("provider_error", "the SAPI provider is only available on Windows", 501);
  }
}

interface RunResult {
  code: number;
  stdout: string;
  stderr: string;
}

function runPowerShell(
  script: string,
  options: { stdin?: string; env?: Record<string, string>; timeoutMs: number },
): Promise<RunResult> {
  return new Promise((resolve, reject) => {
    const child = spawn(
      "powershell.exe",
      ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
      {
        windowsHide: true,
        env: { ...process.env, ...options.env },
      },
    );

    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      child.kill();
      reject(new OmallaError("timeout", "SAPI process exceeded its time budget", 504));
    }, options.timeoutMs);

    child.stdout.on("data", (chunk: Buffer) => {
      stdout += chunk.toString("utf8");
    });
    child.stderr.on("data", (chunk: Buffer) => {
      stderr += chunk.toString("utf8");
    });
    child.on("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      resolve({ code: code ?? 1, stdout, stderr });
    });

    if (options.stdin !== undefined) {
      child.stdin.write(options.stdin, "utf8");
    }
    child.stdin.end();
  });
}

function abortError(): Error {
  const error = new Error("aborted");
  error.name = "AbortError";
  return error;
}
