from core.state import ComplianceAgentState
import re
from typing import List


def compliance_agent(state: ComplianceAgentState) -> dict:
    output = state["sanitized_output"]
    
    print(f"\n{'='*60}")
    print(f"[COMPLIANCE] Scanning ({len(output)} chars)")
    print(f"[COMPLIANCE] State access: {list(state.keys())}")
    print(f"{'='*60}")
    
    flags = []
    
    ssn_patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b',
        r'\b\d{9}\b',
        r'\b\d{3}\s\d{2}\s\d{4}\b'
    ]
    
    for pattern in ssn_patterns:
        if re.search(pattern, output):
            output = re.sub(pattern, '[REDACTED]', output)
            flags.append("ssn_removed")
            print("[COMPLIANCE] ⚠️  SSN detected and removed")
    
    cc_pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
    
    if re.search(cc_pattern, output):
        output = re.sub(cc_pattern, '[REDACTED]', output)
        flags.append("credit_card_removed")
        print("[COMPLIANCE] ⚠️  Credit card detected and removed")
    
    password_patterns = [
        r'password\s*[:=]\s*\S+',
        r'pwd\s*[:=]\s*\S+'
    ]
    
    for pattern in password_patterns:
        if re.search(pattern, output, re.IGNORECASE):
            output = re.sub(pattern, '[PASSWORD REDACTED]', output, flags=re.IGNORECASE)
            flags.append("password_removed")
            print("[COMPLIANCE] ⚠️  Password detected and removed")
    
    profanity_list = ["badword1", "badword2"]
    
    for word in profanity_list:
        if word in output.lower():
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            output = pattern.sub("***", output)
            flags.append("profanity_filtered")
    
    result = {
        "sanitized_output": output,
        "compliance_flags": flags
    }
    
    if flags:
        result["analytics_events"] = [{
            "event": "compliance_issue_detected",
            "flags": flags,
            "severity": "critical" if "ssn_removed" in flags else "medium"
        }]
        print(f"[COMPLIANCE] Issues found: {', '.join(flags)}")
    else:
        print("[COMPLIANCE] ✅ No issues detected")
    
    print(f"{'='*60}\n")
    
    return result
