# Security Policy — Android-MCP

We take the security of **Android-MCP** seriously. This project provides programmatic control over mobile operating system layers and implements strict Zero-Trust guardrails to protect host infrastructure and user privacy.

---

## 1. Supported Versions

Security updates and patches are actively provided for the following release branches:

| Version | Supported | Notes |
| :--- | :---: | :--- |
| `0.3.x` | ✅ Yes | Current stable release with Enterprise Guardrails. |
| `0.2.x` | ⚠️ Security Patches Only | Critical vulnerability fixes only. |
| `< 0.2.0` | ❌ No | Legacy preview releases. Please upgrade to `>= 0.3.0`. |

---

## 2. Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, SSRF bypass, or potential shell injection vector, please report it via one of the following channels:

* **Email**: `security@buhozurdo.com` (or contact maintainers directly at `raelcorrales@gmail.com`)
* **GitHub Private Advisory**: Open a draft security advisory under the **Security** tab of the GitHub repository.

### What to Include in Your Report
To help us triage and resolve the issue quickly, please include:
1. A clear description of the vulnerability and its potential impact.
2. Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
3. The affected component (`guardrails/engine.py`, `adb_client.py`, `ui_parser.py`, etc.).
4. Any proposed remediation or patch, if available.

---

## 3. Security Response Timeline (SLA)

* **Acknowledgment**: Within **24 hours** of initial receipt.
* **Triage & Assessment**: Within **48 hours** with severity classification (CVSS 3.1).
* **Fix & Remediation**: Targeted release of a patch within **7 business days** (or 48 hours for critical zero-day vulnerabilities).
* **Public Disclosure**: Coordinated disclosure after the patch has been published.

---

## 4. Built-in Security Design Principles

* **Localhost-Only ADB Protocol**: The ADB port (`5555`) must never be bound to `0.0.0.0` or exposed publicly.
* **Anti-SSRF Policy**: Network requests for APK downloads strictly block cloud metadata services (`169.254.169.254`) and private RFC 1918 subnets.
* **PII Redaction**: Personal identifiers and payment card numbers are automatically masked before logging or LLM transmission.
