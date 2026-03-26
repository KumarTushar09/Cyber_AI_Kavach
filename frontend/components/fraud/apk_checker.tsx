"use client";

import { useState } from "react";
import { analyzeAPK } from "../../services/api_client";

export function APKChecker() {
  const [apkName, setApkName] = useState("");
  const [financialImpact, setFinancialImpact] = useState("GT_1M");
  const [sensitiveData, setSensitiveData] = useState("REGULATED_HIGHLY_SENSITIVE");
  const [repeatOffender, setRepeatOffender] = useState("THREE_PLUS_12M");
  const [result, setResult] = useState<any>(null);

  return (
    <div className="card">
      <h3>APK Fraud Check</h3>
      <input placeholder="app-release.apk" value={apkName} onChange={(e) => setApkName(e.target.value)} />
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
        <button
          onClick={async () =>
            setResult(
              await analyzeAPK(apkName, {
                financial_impact_band: financialImpact,
                sensitive_data_exposure: sensitiveData,
                repeat_offender_pattern: repeatOffender
              })
            )
          }
        >
          Analyze APK
        </button>
      </div>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
