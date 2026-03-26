"use client";

import { useState } from "react";

import { uploadForAnalysis } from "../../services/api_client";

export function FileUpload() {
  const [analysisType, setAnalysisType] = useState<"url" | "sms" | "apk">("sms");
  const [financialImpact, setFinancialImpact] = useState("FROM_10K_TO_100K");
  const [sensitiveData, setSensitiveData] = useState("INTERNAL_ONLY");
  const [repeatOffender, setRepeatOffender] = useState("FIRST_TIME");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);

  const submit = async () => {
    if (!selectedFile) {
      setResult({ status: "error", message: "Please select a file first." });
      return;
    }

    const response = await uploadForAnalysis(selectedFile, analysisType, {
      financial_impact_band: financialImpact,
      sensitive_data_exposure: sensitiveData,
      repeat_offender_pattern: repeatOffender,
    });
    setResult(response);
  };

  return (
    <div className="card">
      <h3>Upload For Analysis</h3>
      <div className="grid two">
        <select value={analysisType} onChange={(e) => setAnalysisType(e.target.value as "url" | "sms" | "apk")}>
          <option value="url">URL</option>
          <option value="sms">SMS</option>
          <option value="apk">APK</option>
        </select>
        <input type="file" onChange={(e) => setSelectedFile(e.target.files?.[0] || null)} />
      </div>
      <div className="grid two" style={{ marginTop: 12 }}>
        <select value={financialImpact} onChange={(e) => setFinancialImpact(e.target.value)}>
          <option value="LT_10K">Financial: &lt; $10K</option>
          <option value="FROM_10K_TO_100K">Financial: $10K-$100K</option>
          <option value="FROM_100K_TO_1M">Financial: $100K-$1M</option>
          <option value="GT_1M">Financial: &gt; $1M</option>
        </select>
        <select value={sensitiveData} onChange={(e) => setSensitiveData(e.target.value)}>
          <option value="NONE">Data: No sensitive data</option>
          <option value="INTERNAL_ONLY">Data: Internal-only</option>
          <option value="CONFIDENTIAL">Data: Confidential (PII/internal IP)</option>
          <option value="REGULATED_HIGHLY_SENSITIVE">Data: Regulated/highly sensitive</option>
        </select>
      </div>
      <div className="grid two" style={{ marginTop: 12 }}>
        <select value={repeatOffender} onChange={(e) => setRepeatOffender(e.target.value)}>
          <option value="FIRST_TIME">Repeat: First-time event</option>
          <option value="SECOND_INCIDENT_12M">Repeat: Second incident in 12 months</option>
          <option value="THREE_PLUS_12M">Repeat: Three or more in 12 months</option>
        </select>
        <button onClick={submit}>Upload And Analyze</button>
      </div>
      <p>S3 upload is attempted when bucket env values are configured.</p>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
