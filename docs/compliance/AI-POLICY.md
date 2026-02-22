# AI Policy (EU AI Act Alignment)

**Document ID:** F-09-AI-POLICY  
**Version:** 1.0  
**Applies to:** Convergio AI agent orchestration platform  
**Last Updated:** 2026-02-22

> This policy defines how Convergio aligns AI governance with the EU AI Act framework and associated trustworthy AI expectations.

## 1) Purpose

Convergio coordinates multiple AI agents for planning, execution, and decision support. This policy establishes controls for:

- Risk classification and use-case gating
- Human oversight
- Transparency to users
- Logging, monitoring, and traceability
- Safety and misuse prevention

## 2) AI System Classification Approach

Convergio treats workloads by intended use and impact:

- **Minimal/limited risk:** productivity workflows, summarization, drafting, internal automations.
- **Potential high-risk context:** workflows used in regulated decisions (employment, credit, healthcare, public services, etc.).
- **Prohibited use:** social scoring, manipulative exploitation, or uses forbidden by applicable law.

Convergio defaults to **limited-risk platform behavior** but requires customer controls and contractual restrictions for sensitive domains.

## 3) EU AI Act Alignment Controls

### 3.1 Transparency

Convergio commits to:

- Clearly indicating AI-assisted outputs in product UX/API where applicable
- Providing provenance and workflow traces for agent actions
- Documenting known limitations and model uncertainty

### 3.2 Human Oversight

Convergio supports:

- Human-in-the-loop approvals for sensitive actions
- Escalation/override controls
- Configurable approval gates and review checkpoints

### 3.3 Risk Management

Convergio uses a continuous lifecycle model:

1. Identify use case and potential harms
2. Classify risk and required controls
3. Apply safeguards (policy, product, operational)
4. Monitor outcomes and incidents
5. Improve controls and documentation

### 3.4 Technical Robustness and Safety

- Guardrails on tool usage and outbound actions
- Reliability checks and fallback behavior
- Monitoring for failure patterns and unsafe outputs
- Access boundaries between tenants and roles

### 3.5 Record-Keeping and Auditability

- Logs of prompts, tool calls, outputs, and approvals (as configured)
- Change history for key policies/configuration
- Support for compliance evidence generation

## 4) Responsibilities

- **Convergio (provider/platform operator):** provide secure architecture, governance controls, auditability, and transparent documentation.
- **Customer (deployer/controller):** define lawful use, classify downstream high-risk use cases, configure oversight, and ensure domain compliance.

## 5) Prohibited and Restricted Use

Customers must not use Convergio for illegal or prohibited AI practices. Restricted domains require documented risk assessment, enhanced human oversight, and legal review before production use.

## 6) Data and Model Governance

- Minimize personal data sent to models and tools
- Apply retention limits and access controls
- Avoid submitting sensitive data unless necessary and authorized
- Track provider/model usage by feature where possible

## 7) Incident and Harm Response

Convergio maintains procedures to:

- Receive and triage AI safety incidents
- Contain harmful behavior promptly
- Notify impacted parties according to legal/contractual obligations
- Correct root causes and update controls

## 8) Compliance Lifecycle

- Initial policy baseline before release
- Periodic reviews (minimum annually)
- Triggered reviews after major architectural/model/regulatory changes
- Evidence retained for internal and external audits

## 9) Related Documents

- `docs/compliance/GDPR.md`
- `docs/compliance/DPIA.md`
