"use client";

import { useEffect, useRef, useState } from "react";

import {
  analyzeAPK,
  analyzeSMS,
  analyzeURL,
  queryKnowledge,
  synthesizeSpeech,
  translateText,
  uploadForAnalysis,
} from "../../services/api_client";

type PanelKey = "overview" | "knowledge" | "fraud" | "upload";

type Message = {
  id: number;
  role: "assistant" | "user";
  title?: string;
  text: string;
};

type AttachmentItem = {
  id: number;
  name: string;
  size: number;
  type: string;
  file: File;
};

type ChatWorkspaceProps = {
  initialPanel?: PanelKey;
};

const spaces = [
  { name: "Threat Intel", count: "124 notes" },
  { name: "Fraud Playbooks", count: "38 workflows" },
  { name: "User Reports", count: "217 uploads" },
  { name: "Policy Knowledge", count: "19 references" },
];

const recents = ["APK triage flow", "UPI phishing patterns", "Incident intake summary"];

const starterMessages: Message[] = [
  {
    id: 1,
    role: "assistant",
    title: "Cyber AI Kavach",
    text:
      "This is the unified investigation shell. You can search knowledge, run fraud checks, and attach evidence from the same conversation.",
  },
  {
    id: 2,
    role: "assistant",
    title: "Current mode",
    text:
      "The frontend is in preview mode, so all actions return mock responses when backend services are not connected.",
  },
];

const promptSuggestions = [
  "Summarize recent phishing indicators",
  "Check whether this SMS looks suspicious",
  "Create an investigation brief from attached files",
];

const riskDefaults = {
  financial_impact_band: "FROM_10K_TO_100K",
  sensitive_data_exposure: "INTERNAL_ONLY",
  repeat_offender_pattern: "FIRST_TIME",
};

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

const MAX_RECORDING_DURATION_MS = 60_000;
const STT_FALLBACK_TEXT = "I could not transcribe that audio. Please type your question in the input box and send it.";

function formatFileSize(size: number) {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function fileLabel(type: string) {
  if (type.includes("image")) {
    return "IMG";
  }
  if (type.includes("pdf")) {
    return "PDF";
  }
  if (type.includes("text")) {
    return "TXT";
  }
  return "FILE";
}

export function ChatWorkspace({ initialPanel = "overview" }: ChatWorkspaceProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recorderChunksRef = useRef<Blob[]>([]);
  const recordingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activePanel, setActivePanel] = useState<PanelKey>(initialPanel);
  const [messages, setMessages] = useState<Message[]>(starterMessages);
  const [draft, setDraft] = useState("");
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
  const [knowledgePrompt, setKnowledgePrompt] = useState("What are the latest patterns for account takeover fraud?");
  const [urlInput, setUrlInput] = useState("https://secure-alert-payments.example");
  const [smsInput, setSmsInput] = useState("Your KYC expires today. Click this link to avoid account suspension.");
  const [apkInput, setApkInput] = useState("quick-loan-release.apk");
  const [toolResult, setToolResult] = useState<string>("");
  const [ttsLanguage, setTtsLanguage] = useState("en");
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessingVoice, setIsProcessingVoice] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSynthesizing, setIsSynthesizing] = useState(false);

  const speechAudioRef = useRef<HTMLAudioElement | null>(null);
  const speechObjectUrlRef = useRef<string | null>(null);

  const pushMessage = (message: Omit<Message, "id">) => {
    setMessages((prev) => [...prev, { ...message, id: prev.length + 1 }]);
  };

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

  const playResultAudio = async () => {
    const text = toolResult.trim();
    if (!text) {
      return;
    }

    if (isSpeaking) {
      stopSpeaking();
      return;
    }

    try {
      setIsSynthesizing(true);
      const speechText = await translateText(text, ttsLanguage);

      // Sarvam generated-audio path is configured for en-IN in this setup.
      // For non-English choices, speak translated text through browser voices.
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

  useEffect(() => {
    return () => {
      stopSpeaking();
    };
  }, []);

  const handleAttach = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const nextFiles = Array.from(event.target.files || []).map((file, index) => ({
      id: Date.now() + index,
      name: file.name,
      size: file.size,
      type: file.type,
      file,
    }));

    setAttachments((prev) => [...prev, ...nextFiles]);
  };

  const removeAttachment = (attachmentId: number) => {
    setAttachments((prev) => prev.filter((item) => item.id !== attachmentId));
  };

  const sendChat = async () => {
    const trimmed = draft.trim();
    if (!trimmed && attachments.length === 0) {
      return;
    }

    const summary = attachments.length > 0 ? ` Attached: ${attachments.map((item) => item.name).join(", ")}.` : "";
    pushMessage({ role: "user", text: `${trimmed || "Please review these files."}${summary}` });

    const response = await queryKnowledge(trimmed || "Summarize the attached evidence.");
    pushMessage({
      role: "assistant",
      title: attachments.length > 0 ? "Evidence ready" : "Knowledge response",
      text: response?.data?.answer || "Preview response generated.",
    });

    setDraft("");
    setAttachments([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const runKnowledgePrompt = async () => {
    pushMessage({ role: "user", text: knowledgePrompt });
    const response = await queryKnowledge(knowledgePrompt);
    const answer = response?.data?.answer || "No response available.";
    pushMessage({ role: "assistant", title: "Knowledge base", text: answer });
    setToolResult(answer);
    setActivePanel("knowledge");
  };

  const runFraudTool = async (kind: "url" | "sms" | "apk") => {
    if (kind === "url") {
      const response = await analyzeURL(urlInput, riskDefaults);
      const result = JSON.stringify(response, null, 2);
      pushMessage({ role: "user", text: `Analyze URL: ${urlInput}` });
      pushMessage({ role: "assistant", title: "URL analysis", text: result });
      setToolResult(result);
      return;
    }

    if (kind === "sms") {
      const response = await analyzeSMS(smsInput, riskDefaults);
      const result = JSON.stringify(response, null, 2);
      pushMessage({ role: "user", text: `Analyze SMS: ${smsInput}` });
      pushMessage({ role: "assistant", title: "SMS analysis", text: result });
      setToolResult(result);
      return;
    }

    const response = await analyzeAPK(apkInput, riskDefaults);
    const result = JSON.stringify(response, null, 2);
    pushMessage({ role: "user", text: `Analyze APK: ${apkInput}` });
    pushMessage({ role: "assistant", title: "APK analysis", text: result });
    setToolResult(result);
  };

  const uploadEvidence = async () => {
    if (attachments.length === 0) {
      setToolResult("Add at least one file with the + button first.");
      return;
    }

    const response = await uploadForAnalysis(attachments[0].file, "apk", riskDefaults);
    const result = JSON.stringify(response, null, 2);
    pushMessage({ role: "user", text: `Upload evidence: ${attachments[0].name}` });
    pushMessage({ role: "assistant", title: "Upload result", text: result });
    setToolResult(result);
    setActivePanel("upload");
  };

  const stopVoiceRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
  };

  const startVoiceRecording = async () => {
    if (isProcessingVoice) {
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      recorderChunksRef.current = [];
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          recorderChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        setIsRecording(false);
        if (recordingTimeoutRef.current) {
          clearTimeout(recordingTimeoutRef.current);
          recordingTimeoutRef.current = null;
        }
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(recorderChunksRef.current, { type: recorder.mimeType || "audio/webm" });
        if (!blob.size) {
          return;
        }

        try {
          setIsProcessingVoice(true);
          // Voice query feature not yet implemented in client
          // const response = await queryKnowledgeVoice(blob);
          // For now, show fallback message
          const fallbackMessage = "Voice query feature coming soon. Please use text input for now.";
          pushMessage({ role: "assistant", title: "Voice assistant", text: fallbackMessage });
          setToolResult(fallbackMessage);
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : "Voice request failed.";
          const fallbackMessage = `${errorMessage}\n${STT_FALLBACK_TEXT}`;
          pushMessage({ role: "assistant", title: "Voice assistant", text: fallbackMessage });
          setToolResult(fallbackMessage);
        } finally {
          setIsProcessingVoice(false);
        }
      };

      recorder.start();
      setIsRecording(true);
      recordingTimeoutRef.current = setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
          mediaRecorderRef.current.stop();
        }
      }, MAX_RECORDING_DURATION_MS);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Microphone permission is required.";
      pushMessage({ role: "assistant", title: "Voice assistant", text: message });
      setToolResult(message);
    }
  };

  const handleVoiceAction = async () => {
    if (isRecording) {
      stopVoiceRecording();
      return;
    }
    await startVoiceRecording();
  };

  return (
    <main className={`workspace-shell ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}>
      <aside className="workspace-sidebar">
        <div className="brand-block">
          <div className="brand-mark">CK</div>
          {!sidebarCollapsed ? (
            <div>
              <p className="eyebrow">Cyber AI Kavach</p>
              <h1>Knowledge Copilot</h1>
            </div>
          ) : null}
        </div>

        <button className="collapse-toggle" onClick={() => setSidebarCollapsed((prev) => !prev)}>
          {sidebarCollapsed ? ">" : "<"}
        </button>

        {!sidebarCollapsed ? (
          <>
            <button className="sidebar-primary" onClick={() => setActivePanel("overview")}>
              New investigation
            </button>

            <section className="sidebar-section">
              <div className="section-heading">
                <span>Workspace modes</span>
              </div>
              <div className="space-list">
                <button className={`space-card ${activePanel === "knowledge" ? "active" : ""}`} onClick={() => setActivePanel("knowledge")}>
                  <strong>Knowledge base</strong>
                  <span>Search policies, intel, and notes</span>
                </button>
                <button className={`space-card ${activePanel === "fraud" ? "active" : ""}`} onClick={() => setActivePanel("fraud")}>
                  <strong>Fraud tools</strong>
                  <span>Run URL, SMS, and APK checks</span>
                </button>
                <button className={`space-card ${activePanel === "upload" ? "active" : ""}`} onClick={() => setActivePanel("upload")}>
                  <strong>Uploads</strong>
                  <span>Stage evidence and review files</span>
                </button>
              </div>
            </section>

            <section className="sidebar-section">
              <div className="section-heading">
                <span>Knowledge spaces</span>
              </div>
              <div className="space-list">
                {spaces.map((space) => (
                  <button key={space.name} className="space-card">
                    <strong>{space.name}</strong>
                    <span>{space.count}</span>
                  </button>
                ))}
              </div>
            </section>

            <section className="sidebar-section">
              <div className="section-heading">
                <span>Recent threads</span>
              </div>
              <div className="recent-list">
                {recents.map((item) => (
                  <button key={item} className="recent-item">
                    {item}
                  </button>
                ))}
              </div>
            </section>
          </>
        ) : (
          <div className="collapsed-icons">
            <button className="collapsed-pill" onClick={() => setActivePanel("overview")}>C</button>
            <button className="collapsed-pill" onClick={() => setActivePanel("knowledge")}>K</button>
            <button className="collapsed-pill" onClick={() => setActivePanel("fraud")}>F</button>
            <button className="collapsed-pill" onClick={() => setActivePanel("upload")}>U</button>
          </div>
        )}
      </aside>

      <section className="workspace-main">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">Unified investigation surface</p>
            <h2>Chat, knowledge base, fraud analysis, and evidence upload in one interface.</h2>
          </div>
          <nav className="header-links">
            <a href="/">Home</a>
            <a href="/knowledge-assistant">Knowledge</a>
            <a href="/fraud-check">Fraud</a>
            <a href="/upload">Uploads</a>
          </nav>
        </header>

        <section className="hero-panel">
          <div>
            <p className="eyebrow">Current focus</p>
            <h3>{activePanel === "overview" ? "Conversation hub" : `${activePanel} workspace`}</h3>
            <p>
              Use the left rail to switch context, the + button to stage files, and the right rail to run knowledge or fraud actions without leaving the chat.
            </p>
          </div>
          <div className="hero-stats">
            <div>
              <strong>{spaces.length}</strong>
              <span>knowledge spaces</span>
            </div>
            <div>
              <strong>{attachments.length}</strong>
              <span>staged files</span>
            </div>
            <div>
              <strong>{messages.length}</strong>
              <span>conversation entries</span>
            </div>
          </div>
        </section>

        <div className="workspace-content-grid">
          <section className="conversation-card">
            <div className="prompt-strip">
              {promptSuggestions.map((item) => (
                <button key={item} className="prompt-chip" onClick={() => setDraft(item)}>
                  {item}
                </button>
              ))}
            </div>

            <div className="message-list">
              {messages.map((message) => (
                <article key={message.id} className={`message-row ${message.role}`}>
                  <div className="message-avatar">{message.role === "assistant" ? "AI" : "You"}</div>
                  <div className="message-body">
                    {message.title ? <p className="message-title">{message.title}</p> : null}
                    <p>{message.text}</p>
                  </div>
                </article>
              ))}
            </div>

            {attachments.length > 0 ? (
              <div className="attachment-tray attachment-grid">
                {attachments.map((attachment) => (
                  <div key={attachment.id} className="attachment-card">
                    <div className="attachment-icon">{fileLabel(attachment.type)}</div>
                    <div className="attachment-copy">
                      <strong>{attachment.name}</strong>
                      <span>{formatFileSize(attachment.size)}</span>
                    </div>
                    <button className="attachment-remove" onClick={() => removeAttachment(attachment.id)}>
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            ) : null}

            <div className="composer-shell">
              <input ref={fileInputRef} type="file" multiple hidden onChange={handleFileChange} />
              <button className="attach-button" onClick={handleAttach} aria-label="Attach files">
                +
              </button>
              <button className="attach-button" onClick={handleVoiceAction} aria-label="Record voice query" disabled={isProcessingVoice}>
                {isRecording ? "Stop" : "Mic"}
              </button>
              <textarea
                className="composer-input"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Ask about fraud indicators, search the knowledge base, or attach evidence..."
                rows={1}
              />
              <button className="send-button" onClick={sendChat}>
                {isProcessingVoice ? "Working..." : "Send"}
              </button>
            </div>
          </section>

          <aside className="context-rail">
            <div className="context-tabs">
              <button className={activePanel === "knowledge" ? "active" : ""} onClick={() => setActivePanel("knowledge")}>Knowledge</button>
              <button className={activePanel === "fraud" ? "active" : ""} onClick={() => setActivePanel("fraud")}>Fraud</button>
              <button className={activePanel === "upload" ? "active" : ""} onClick={() => setActivePanel("upload")}>Upload</button>
            </div>

            {(activePanel === "overview" || activePanel === "knowledge") ? (
              <section className="context-card">
                <p className="eyebrow">Knowledge search</p>
                <h3>Ask the knowledge base</h3>
                <textarea value={knowledgePrompt} onChange={(event) => setKnowledgePrompt(event.target.value)} rows={4} />
                <button onClick={runKnowledgePrompt}>Search knowledge</button>
              </section>
            ) : null}

            {(activePanel === "overview" || activePanel === "fraud") ? (
              <section className="context-card">
                <p className="eyebrow">Fraud analysis</p>
                <h3>Run quick checks</h3>
                <label className="mini-label">URL</label>
                <input value={urlInput} onChange={(event) => setUrlInput(event.target.value)} />
                <button onClick={() => runFraudTool("url")}>Analyze URL</button>
                <label className="mini-label">SMS</label>
                <textarea value={smsInput} onChange={(event) => setSmsInput(event.target.value)} rows={3} />
                <button onClick={() => runFraudTool("sms")}>Analyze SMS</button>
                <label className="mini-label">APK</label>
                <input value={apkInput} onChange={(event) => setApkInput(event.target.value)} />
                <button onClick={() => runFraudTool("apk")}>Analyze APK</button>
              </section>
            ) : null}

            {(activePanel === "overview" || activePanel === "upload") ? (
              <section className="context-card">
                <p className="eyebrow">Evidence staging</p>
                <h3>Upload area</h3>
                <p className="context-copy">Use the + button below the chat to add files, then send them or upload the first staged file.</p>
                <button onClick={uploadEvidence}>Upload staged evidence</button>
              </section>
            ) : null}

            <section className="context-card result-card">
              <p className="eyebrow">Latest output</p>
              <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
                <label htmlFor="chat-tts-language" className="mini-label" style={{ marginBottom: 0 }}>
                  TTS
                </label>
                <select
                  id="chat-tts-language"
                  value={ttsLanguage}
                  onChange={(event) => setTtsLanguage(event.target.value)}
                  style={{ flex: 1, minWidth: 0 }}
                >
                  {TTS_LANGUAGES.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.label}
                    </option>
                  ))}
                </select>
                <button
                  onClick={playResultAudio}
                  disabled={isSynthesizing || !toolResult.trim()}
                  title={isSpeaking ? "Stop audio" : "Listen to latest output"}
                  aria-label={isSpeaking ? "Stop audio" : "Listen to latest output"}
                >
                  {isSynthesizing ? "..." : isSpeaking ? "Stop" : "🔊"}
                </button>
              </div>
              <pre>{toolResult || "Run a knowledge, fraud, or upload action to see results here."}</pre>
            </section>
          </aside>
        </div>
      </section>
    </main>
  );
}