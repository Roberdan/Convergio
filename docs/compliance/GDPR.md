# GDPR Compliance Policy

**Document ID:** F-09-GDPR  
**Version:** 1.0  
**Applies to:** Convergio platform and AI agent orchestration services  
**Last Updated:** 2026-02-22

> This document describes Convergio's GDPR approach for EU/EEA users. It is an operational policy and implementation baseline, not legal advice.

## 1) Scope and Roles

Convergio is an AI agent orchestration platform that processes user-provided business, operational, and technical data.

- **Data Controller:** The customer organization for data submitted to Convergio on its own behalf.
- **Data Processor:** Convergio when processing customer data under customer instructions.
- **Sub-processors:** Infrastructure and model providers used to deliver the service.

Convergio supports GDPR-aligned processing under Article 28 via contractual and technical safeguards.

## 2) GDPR Principles Applied

Convergio aligns processing with GDPR principles:

1. **Lawfulness, fairness, transparency** — users are informed about processing purposes and data flows.
2. **Purpose limitation** — data is processed only for requested orchestration workflows and platform operations.
3. **Data minimization** — customers are encouraged to send only necessary data; retention controls are implemented.
4. **Accuracy** — users can correct profile/account metadata and re-run workflows with updated data.
5. **Storage limitation** — retention schedules and deletion procedures apply to logs, conversations, and outputs.
6. **Integrity and confidentiality** — encryption, access controls, and auditability protect data.
7. **Accountability** — records, policies, and assessments are maintained.

## 3) Lawful Bases

Depending on use case, Convergio supports processing under:

- **Contract performance** (service delivery)
- **Legitimate interests** (security, abuse prevention, reliability)
- **Legal obligations** (financial/audit recordkeeping)
- **Consent** when required for optional features or integrations

Customers remain responsible for selecting appropriate lawful basis in their deployments.

## 4) Data Categories Processed

Typical categories include:

- Account and tenant metadata (name, email, role, org)
- User prompts, agent messages, and workflow context
- Uploaded files and generated outputs
- System telemetry and security logs
- Billing and usage metadata

Convergio is designed to avoid collecting special-category data unless explicitly provided by customers.

## 5) Data Subject Rights (Articles 12–23)

Convergio supports controller obligations for the following rights:

- Right to be informed
- Right of access
- Right to rectification
- Right to erasure
- Right to restriction of processing
- Right to data portability
- Right to object
- Rights related to automated decision-making and profiling

### Operational handling

- Requests are logged and tracked with timestamps.
- Identity verification is required before fulfillment.
- Standard response target: within **30 days**, unless extension is legally justified.
- Processor-side assistance is provided to controllers through support workflows and data export/deletion tooling.

## 6) International Data Transfers

Where data leaves the EU/EEA, Convergio applies appropriate safeguards, including one or more of:

- Standard Contractual Clauses (SCCs)
- Adequacy decisions
- Supplementary technical measures (encryption, strict access controls)

Regional deployment options should be used where available to reduce transfer risk.

## 7) Security Measures

Convergio implements risk-based controls such as:

- Encryption in transit (TLS) and at rest where supported
- Role-based access control and least privilege
- Audit logging and traceability for agent actions
- Incident detection and response procedures
- Secrets and key management practices
- Dependency and vulnerability management

## 8) Data Processing Agreement (DPA)

Convergio provides a DPA that includes:

- Subject matter and duration of processing
- Nature and purpose of processing
- Types of personal data and data subject categories
- Processor obligations and confidentiality
- Sub-processor controls and notification commitments
- Assistance with rights requests and breach response
- Return/deletion commitments at end of service
- Audit and information rights

DPA execution is required for production processing of customer personal data in regulated contexts.

## 9) Personal Data Breach Notification

Convergio maintains an incident response process aligned to GDPR Articles 33 and 34:

- Detect, classify, contain, and remediate incidents
- Notify affected controllers without undue delay
- Share known impact, categories of data, likely consequences, and mitigation steps
- Maintain breach records for accountability

## 10) Retention and Deletion

- Data retention is tied to contractual needs and defined policy windows.
- Customers can request deletion/export according to contract and legal constraints.
- Backups follow scheduled lifecycle deletion.

## 11) Governance and Review

- Policy owner: Security & Compliance
- Review cadence: at least annually or upon material architecture/regulatory change
- Related documents: `docs/compliance/AI-POLICY.md`, `docs/compliance/DPIA.md`
