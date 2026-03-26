const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api/proxy";
const FRONTEND_ONLY = process.env.NEXT_PUBLIC_FRONTEND_ONLY === "true";

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

function normalizeLanguageCode(code: string) {
  const normalized = (code || "en").trim();
  return TTS_LANGUAGE_TO_LOCALE[normalized] || normalized;
}

export type RiskInput = {
  financial_impact_band: string;
  sensitive_data_exposure: string;
  repeat_offender_pattern: string;
};

function mockRiskResponse(kind: "url" | "sms" | "apk", value: string) {
  return {
    status: "success",
    source: "frontend-mock",
    data: {
      analysis_type: kind,
      input: value,
      verdict: "suspicious",
      risk_score: 78,
      confidence: 0.91,
      recommendation: "Review manually before allowing user action."
    }
  };
}

function mockKnowledgeResponse(question: string) {
  return {
    status: "success",
    source: "frontend-mock",
    data: {
      question,
      answer:
        "Mock mode response: this UI is working without backend connectivity. Connect backend later for live knowledge retrieval."
    }
  };
}

async function postJson(path: string, payload: Record<string, unknown>, fallback: unknown) {
  if (FRONTEND_ONLY) {
    return fallback;
  }

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      const body = await response.text();
      throw new Error(`Backend request failed (${response.status}): ${body}`);
    }
    return await response.json();
  } catch {
    return fallback;
  }
}

export async function uploadForAnalysis(file: File, analysisType: "url" | "sms" | "apk", riskInput: RiskInput) {
  if (FRONTEND_ONLY) {
    return mockRiskResponse(analysisType, file.name);
  }

  const formData = new FormData();
  formData.append("analysis_type", analysisType);
  formData.append("financial_impact_band", riskInput.financial_impact_band);
  formData.append("sensitive_data_exposure", riskInput.sensitive_data_exposure);
  formData.append("repeat_offender_pattern", riskInput.repeat_offender_pattern);
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE}/upload/file`, {
      method: "POST",
      body: formData
    });
    return await response.json();
  } catch {
    return mockRiskResponse(analysisType, file.name);
  }
}



export async function analyzeURL(url: string, risk_input?: RiskInput, compact = true) {
  const compactParam = compact ? "?compact=true" : "?compact=false";
  const payload: Record<string, unknown> = { url };
  if (risk_input) {
    payload.risk_input = risk_input;
  }
  if (FRONTEND_ONLY) {
    return mockRiskResponse("url", url);
  }

  const response = await fetch(`${API_BASE}/analyze/url${compactParam}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`URL analysis failed (${response.status}): ${body}`);
  }

  return await response.json();
}

export async function analyzeSMS(sms_text: string, risk_input: RiskInput) {
  return postJson("/analyze/sms", { sms_text, risk_input }, mockRiskResponse("sms", sms_text));
}

export async function analyzeAPK(apk_name: string, risk_input: RiskInput) {
  return postJson("/analyze/apk", { apk_name, risk_input }, mockRiskResponse("apk", apk_name));
}

export async function queryKnowledge(question: string) {
  return postJson("/knowledge/query", { question }, mockKnowledgeResponse(question));
}

export async function transcribeAudio(audioBlob: Blob) {
  if (FRONTEND_ONLY) {
    return "https://example.com";
  }

  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");

  const response = await fetch(`${API_BASE}/voice/transcribe`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const body = await response.text();
    const loweredBody = body.toLowerCase();
    if (loweredBody.includes("unable to transcribe audio")) {
      throw new Error("Could not recognized speak again.");
    }
    throw new Error(`STT failed (${response.status}): ${body}`);
  }

  const payload = await response.json();
  const text = payload?.data?.text;
  return typeof text === "string" ? text : "";
}

export async function synthesizeSpeech(text: string, target_language_code: string = "en") {
  if (FRONTEND_ONLY) {
    throw new Error("TTS is unavailable in frontend-only mode.");
  }

  const normalizedCode = normalizeLanguageCode(target_language_code);

  const response = await fetch(`${API_BASE}/voice/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, target_language_code: normalizedCode }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`TTS failed (${response.status}): ${body}`);
  }

  return await response.blob();
}

export async function translateText(text: string, target_language_code: string = "en") {
  const normalizedCode = normalizeLanguageCode(target_language_code);
  if (!text.trim() || normalizedCode.toLowerCase() === "en-in") {
    return text;
  }

  if (FRONTEND_ONLY) {
    return text;
  }

  const response = await fetch(`${API_BASE}/voice/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, target_language_code: normalizedCode }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Translation failed (${response.status}): ${body}`);
  }

  const payload = await response.json();
  const translated = payload?.data?.text;
  return typeof translated === "string" && translated.trim() ? translated : text;
}
