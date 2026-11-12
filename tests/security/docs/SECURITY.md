# HealthGuard AI — Security and Privacy Documentation

**Project:** HealthGuard AI
**Document:** Security Controls and Privacy Practices
**Status:** Portfolio project — development environment
**Data policy:** Synthetic healthcare data only

## 1. Security Objectives

HealthGuard AI implements security controls to protect sensitive healthcare-related information, enforce tenant isolation, restrict AI provider access, and reduce risks from malicious inputs.

The system uses a human-in-the-loop workflow. AI agents provide recommendations; authorized human reviewers make final authorization decisions.

## 2. Data Classification

The application classifies data into five categories:

| Classification | Description                              |
| -------------- | ---------------------------------------- |
| PUBLIC         | Public information                       |
| INTERNAL       | Internal business and policy information |
| PII            | Personally identifiable information      |
| PHI            | Protected health information             |
| SECRET         | Credentials, tokens and secrets          |

Unknown field classifications are rejected by default.

Classification currently relies on field names and nested data structures. It is not a complete content-scanning or de-identification solution.

## 3. AI Provider Authorization

AI calls use centralized provider authorization.

Before data reaches an AI provider, the application checks the task, provider and data classification.

Sensitive data is blocked when the provider is not authorized.

Primary and fallback model calls must follow the same authorization requirements.

The application uses Groq and Google Gemini integrations. Their suitability for real healthcare data has not been established.

## 4. Authentication and Authorization

The application implements:

- JWT-based authentication.
- Token expiration and validation.
- Active-user verification.
- Role-based access control.
- Provider, Reviewer and Admin roles.
- Organization-level tenant isolation.

Database queries must enforce organization ownership.

## 5. Tenant Isolation

Authorization, document, coverage and review operations use organization-scoped access.

Document storage keys include organization and authorization identifiers.

Cross-organization access is covered by automated security tests.

## 6. Prompt Injection and Input Validation

The application implements:

- Untrusted-input serialization.
- Input-size limits.
- Defensive system instructions.
- Evidence identifier validation.
- Citation validation.
- Rejection of unsupported evidence references.

These controls reduce prompt-injection risk but do not guarantee immunity from prompt injection.

## 7. Logging and Privacy

Sensitive logging controls include:

- Redaction of detected email addresses.
- Redaction of detected phone numbers.
- JWT and bearer-token redaction.
- Secret-assignment redaction.
- Generic error messages for selected document-processing failures.

Redaction uses pattern matching and is not comprehensive PHI detection.

Application logs must not contain patient document text, clinical evidence, credentials or raw authorization payloads.

## 8. Database Security

PostgreSQL configuration includes:

- SQL parameter hiding.
- Disabled SQLAlchemy query echo.
- Connection health checks.
- Organization-scoped repository operations.
- PostgreSQL-backed LangGraph checkpointing.

Production deployments should use strong credentials, private networking, encryption in transit, managed backups and controlled migrations.

## 9. Redis Security

Redis configuration includes:

- Password authentication.
- Localhost-only port binding for development.
- Connection and socket timeouts.
- Connection health checks.
- Bounded connection pooling.
- Explicit application shutdown cleanup.

Cache keys include tenant identifiers where applicable.

Policy-search cache keys use HMAC-SHA256. Patient-specific queries must not be cached as general policy-search queries.

Redis is used as a cache, not as durable workflow storage.

## 10. Document and S3 Security

Document storage uses:

- HTTPS-enabled S3 connections.
- Server-side encryption.
- Private bucket access.
- Block Public Access.
- Bucket Owner Enforced ownership.
- Versioning.
- Organization-scoped object keys.
- PDF MIME and signature checks.
- File-size limits.
- Generic processing errors.

Production deployment should additionally implement malware scanning, retention controls, restricted IAM permissions and permanent-deletion procedures.

## 11. Current Limitations

The following controls are not complete production guarantees:

- PII detection and redaction are pattern-based.
- Prompt-injection defenses are not foolproof.
- PDF signature checks do not detect all malicious files.
- S3 versioning requires a separate retention and deletion strategy.
- Automated tests are not an independent penetration test.
- Hosted Redis TLS and production network controls still require deployment verification.
- External AI provider authorization for real healthcare data has not been established.

## 12. Real Healthcare Data Restrictions

This project currently uses synthetic healthcare data only.

Real patient data must remain disabled until the required legal, contractual, technical and operational approvals are completed.

Before processing electronic protected health information, evaluate:

- Applicable covered-entity and business-associate responsibilities.
- Appropriate Business Associate Agreements.
- Exact AI provider products, accounts and configurations.
- Encryption, retention and access controls.
- Infrastructure location and risk analysis.
- Incident response and audit requirements.

No claim of HIPAA compliance or certification is made.

## 13. Security Verification

The automated security test suite currently reports:

- 164 tests passed.
- 0 test failures.

Tests cover authentication, RBAC, provider authorization, data classification, tenant isolation, input validation, prompt-injection defenses, logging, cache keys, Redis lifecycle and document storage.

Passing automated tests does not establish complete security or regulatory compliance.

## 14. Production Readiness Checklist

Before production deployment:

- [ ] Replace development credentials with strong secrets.
- [ ] Configure private networking and TLS.
- [ ] Review provider agreements and data-processing configurations.
- [ ] Configure S3 malware scanning and retention.
- [ ] Complete a security risk assessment.
- [ ] Perform independent penetration testing.
- [ ] Configure centralized audit logging and monitoring.
- [ ] Establish incident response procedures.
- [ ] Verify backup and recovery procedures.
- [ ] Complete required legal and compliance reviews.
