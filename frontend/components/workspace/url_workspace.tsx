"use client";

import { useState, useRef } from "react";

import { analyzeURL, RiskInput, synthesizeSpeech, transcribeAudio, translateText } from "../../services/api_client";

// Sarvam-supported languages (update as needed)
const TTS_LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "Hindi" },
  { code: "ta", label: "Tamil" },
  { code: "te", label: "Telugu" },
  { code: "kn", label: "Kannada" },
  { code: "ml", label: "Malayalam" },
  { code: "bn", label: "Bengali" },
  { code: "gu", label: "Gujarati" },
  { code: "mr", label: "Marathi" },
  { code: "pa", label: "Punjabi" },
  { code: "ur", label: "Urdu" },
  // Add more as supported by Sarvam
];

const TTS_LANGUAGE_TO_LOCALE: Record<string, string> = {
  en: "en-IN",
  hi: "hi-IN",
  ta: "ta-IN",
  te: "te-IN",
  kn: "kn-IN",
  ml: "ml-IN",
  bn: "bn-IN",
  gu: "gu-IN",
  mr: "mr-IN",
  pa: "pa-IN",
  ur: "ur-IN",
};

const initialRiskInput: RiskInput = {
  financial_impact_band: "FROM_10K_TO_100K",
  sensitive_data_exposure: "INTERNAL_ONLY",
  repeat_offender_pattern: "FIRST_TIME",
};

const riskOptions = {
  financial_impact_band: [
    { value: "LT_10K", label: "< $10K" },
    { value: "FROM_10K_TO_100K", label: "$10K-$100K" },
    { value: "FROM_100K_TO_1M", label: "$100K-$1M" },
    { value: "GT_1M", label: "> $1M" },
  ],
  sensitive_data_exposure: [
    { value: "NONE", label: "No sensitive data" },
    { value: "INTERNAL_ONLY", label: "Internal-only data" },
    { value: "CONFIDENTIAL", label: "Confidential data (PII/internal IP)" },
    { value: "REGULATED_HIGHLY_SENSITIVE", label: "Regulated/highly sensitive (PCI/PHI/etc.)" },
  ],
  repeat_offender_pattern: [
    { value: "FIRST_TIME", label: "First-time event" },
    { value: "SECOND_INCIDENT_12M", label: "Second incident within 12 months" },
    { value: "THREE_PLUS_12M", label: "Three or more incidents within 12 months" },
  ],
};

export function UrlWorkspace() {
  const [ttsLanguage, setTtsLanguage] = useState("en");
  const [url, setUrl] = useState("https://www.jssateb.ac.in/");
  const [riskInput, setRiskInput] = useState<RiskInput>(initialRiskInput);
  const [needsRiskInput, setNeedsRiskInput] = useState(false);
  const [result, setResult] = useState("Run URL analysis to start Pass 1 (JSON analysis).");
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const speechAudioRef = useRef<HTMLAudioElement | null>(null);
  const speechObjectUrlRef = useRef<string | null>(null);

  const releaseSpeechObjectUrl = () => {
    if (speechObjectUrlRef.current) {
      URL.revokeObjectURL(speechObjectUrlRef.current);
      speechObjectUrlRef.current = null;
    }
  };

  const stopSpeaking = () => {
    if (speechAudioRef.current) {
      speechAudioRef.current.pause();
      speechAudioRef.current.currentTime = 0;
      speechAudioRef.current = null;
    }
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    releaseSpeechObjectUrl();
    setIsSpeaking(false);
  };

  const startBrowserSpeech = (text: string, languageCode: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      throw new Error("Browser speech synthesis is not supported on this device.");
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = TTS_LANGUAGE_TO_LOCALE[languageCode] || languageCode;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  };

  const analyzeFirstPassForInput = async (inputUrl: string) => {
    const trimmed = inputUrl.trim();
    if (!trimmed) {
      setResult("Please enter a URL first.");
      return;
    }

    setLoading(true);
    try {
      const response = await analyzeURL(trimmed, undefined, true);
      const data = response?.data || {};
      setNeedsRiskInput(Boolean(data?.needs_risk_input));
      setResult(buildDisplayResult(response));
    } catch {
      setResult("URL analysis request failed. Check backend logs and try again.");
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      
      audioChunksRef.current = [];
      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        await sendAudioToBackend(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
    } catch (error) {
      console.error("Microphone access denied:", error);
      alert("Please allow microphone access to use voice input.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendAudioToBackend = async (audioBlob: Blob) => {
    try {
      const transcript = await transcribeAudio(audioBlob);
      if (transcript) {
        setUrl(transcript);
        setResult('Click "Run Pass 1 (URL JSON Analysis)" to start analysis.');
      } else {
        alert("No speech detected. Please try again.");
      }
    } catch (error) {
      console.error("STT error:", error);
      const message = error instanceof Error ? error.message : "Speech-to-text conversion failed. Try again.";
      setResult(`Speech-to-text failed: ${message}`);
      alert(message);
    }
  };

  const normalizeSummary = (text: string): string => {
    return text
      .replace(/\*\*/g, "")
      .replace(/^\s*[-*]\s+/gm, "")
      .replace(/^\s*Summary\s*$/gim, "")
      .trim();
  };

  const buildDisplayResult = (response: any): string => {
    const data = response?.data || {};
    const summary = data?.llm_summary?.response;

    if (summary && String(summary).trim()) {
      return normalizeSummary(String(summary));
    }

    if (data?.needs_risk_input) {
      const rec = data?.pass1?.recommendation || "BLOCK/WARN";
      return `Pass 1 recommendation is ${rec}. Please answer the 3 risk questions below to generate the final report.`;
    }

    return "Unable to generate summary. Please try again.";
  };

  const runFirstPass = async () => {
    await analyzeFirstPassForInput(url);
  };

  const playResultAudio = async () => {
    const text = result.trim();
    if (!text || text === "Run URL analysis to start Pass 1 (JSON analysis).") {
      return;
    }

    if (isSpeaking) {
      stopSpeaking();
      return;
    }

    try {
      setIsSynthesizing(true);
      const speechText = await translateText(text, ttsLanguage);

      // Sarvam setup in this project supports en-IN for generated audio.
      // For other languages, speak the translated text via browser TTS.
      if (ttsLanguage !== "en") {
        stopSpeaking();
        startBrowserSpeech(speechText, ttsLanguage);
        return;
      }

      const audioBlob = await synthesizeSpeech(speechText, ttsLanguage);
      releaseSpeechObjectUrl();
      const objectUrl = URL.createObjectURL(audioBlob);
      speechObjectUrlRef.current = objectUrl;

      const audio = new Audio(objectUrl);
      speechAudioRef.current = audio;
      audio.onended = () => {
        setIsSpeaking(false);
        releaseSpeechObjectUrl();
      };
      audio.onerror = () => {
        stopSpeaking();
      };

      await audio.play();
      setIsSpeaking(true);
    } catch (error) {
      console.error("TTS error:", error);
      stopSpeaking();
      try {
        const speechText = await translateText(text, ttsLanguage);
        startBrowserSpeech(speechText, ttsLanguage);
      } catch (fallbackError) {
        console.error("Browser TTS fallback error:", fallbackError);
        alert("Text-to-speech conversion failed. Try again.");
      }
    } finally {
      setIsSynthesizing(false);
    }
  };

  const runSecondPass = async () => {
    const trimmed = url.trim();
    if (!trimmed) {
      setResult("Please enter a URL first.");
      return;
    }

    setLoading(true);
    try {
      const response = await analyzeURL(trimmed, riskInput, true);
      setNeedsRiskInput(false);
      setResult(buildDisplayResult(response));
    } catch {
      setResult("Risk evaluation request failed. Check backend logs and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ maxWidth: 980, margin: "40px auto", padding: "0 16px" }}>
      <section
        style={{
          background: "#ffffff",
          borderRadius: 16,
          padding: 24,
          border: "1px solid #d5deea",
          boxShadow: "0 12px 24px rgba(16, 21, 31, 0.08)",
        }}
      >
        <p className="eyebrow">Cyber AI Kavach - URL Mode</p>
        <h1 style={{ marginTop: 0 }}>URL Analysis (Two-Pass LLM)</h1>
        <p style={{ color: "#425268" }}>
          Pass 1 generates phishing JSON from the URL prompt. If recommendation is BLOCK/WARN, Pass 2 asks for
          risk-engine inputs and then produces the final summary.
        </p>

        <label htmlFor="url-input" className="mini-label">
          URL to analyze
        </label>
        <input
          id="url-input"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://example.com"
          style={{ width: "100%", marginBottom: 12 }}
        />

        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <label htmlFor="tts-language" style={{ fontSize: 14, marginRight: 8 }}>TTS Language:</label>
          <select
            id="tts-language"
            value={ttsLanguage}
            onChange={e => setTtsLanguage(e.target.value)}
            style={{ padding: "4px 8px", borderRadius: 6, border: "1px solid #d5deea", marginRight: 8 }}
          >
            {TTS_LANGUAGES.map(lang => (
              <option key={lang.code} value={lang.code}>{lang.label}</option>
            ))}
          </select>
          <button
            onClick={isRecording ? stopRecording : startRecording}
            style={{
              background: isRecording ? "#ffeaea" : "#e0f7f4",
              border: `1px solid ${isRecording ? "#ff6b6b" : "#4ecdc4"}`,
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: 20,
              padding: "8px 16px",
              color: isRecording ? "#ff6b6b" : "#4ecdc4",
              display: "flex",
              alignItems: "center"
            }}
            title={isRecording ? "Stop recording" : "Start voice input"}
          >
            🎤
          </button>
          <button onClick={runFirstPass} disabled={loading} style={{ width: "100%" }}>
            {loading ? "Analyzing..." : "Run Pass 1 (URL JSON Analysis)"}
          </button>
          <button
            onClick={playResultAudio}
            disabled={isSynthesizing || loading}
            title={isSpeaking ? "Stop audio" : "Listen to result"}
            style={{
              background: isSpeaking ? "#ffeaea" : "#eef2ff",
              border: `1px solid ${isSpeaking ? "#ff6b6b" : "#6172f3"}`,
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: 20,
              padding: "8px 16px",
              color: isSpeaking ? "#ff6b6b" : "#4f46e5",
              display: "flex",
              alignItems: "center"
            }}
          >
            {isSynthesizing ? "..." : "🔊"}
          </button>
        </div>

        {needsRiskInput ? (
          <div style={{ marginTop: 20, padding: 16, border: "1px solid #d5deea", borderRadius: 12 }}>
            <p className="eyebrow">Risk Engine Input Required</p>
            <p style={{ marginTop: 0, color: "#425268" }}>
              Recommendation is BLOCK/WARN. Please answer these 3 questions for risk evaluation.
            </p>

            <label className="mini-label" htmlFor="financial-impact">
              Financial impact
            </label>
            <select
              id="financial-impact"
              value={riskInput.financial_impact_band}
              onChange={(event) =>
                setRiskInput((prev) => ({ ...prev, financial_impact_band: event.target.value }))
              }
              style={{ width: "100%", marginBottom: 12 }}
            >
              {riskOptions.financial_impact_band.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            <label className="mini-label" htmlFor="sensitive-data">
              Sensitive data exposure
            </label>
            <select
              id="sensitive-data"
              value={riskInput.sensitive_data_exposure}
              onChange={(event) =>
                setRiskInput((prev) => ({ ...prev, sensitive_data_exposure: event.target.value }))
              }
              style={{ width: "100%", marginBottom: 12 }}
            >
              {riskOptions.sensitive_data_exposure.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            <label className="mini-label" htmlFor="repeat-offender">
              Repeat offender pattern
            </label>
            <select
              id="repeat-offender"
              value={riskInput.repeat_offender_pattern}
              onChange={(event) =>
                setRiskInput((prev) => ({ ...prev, repeat_offender_pattern: event.target.value }))
              }
              style={{ width: "100%", marginBottom: 16 }}
            >
              {riskOptions.repeat_offender_pattern.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            <button onClick={runSecondPass} disabled={loading}>
              {loading ? "Evaluating..." : "Run Pass 2 (Risk + Summary)"}
            </button>
          </div>
        ) : null}

        <div style={{ marginTop: 20 }}>
          <p className="eyebrow">Result</p>
          <pre
            style={{
              background: "#0f1722",
              color: "#e6edf7",
              borderRadius: 12,
              padding: 16,
              overflowX: "auto",
              minHeight: 220,
            }}
          >
            {result}
          </pre>
        </div>
      </section>
    </main>
  );
}
