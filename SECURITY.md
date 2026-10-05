# Security Policy

## Supported Versions

We release security patches and updates for the following versions:

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |
| < 0.1.0 | No        |

---

## Reporting a Vulnerability

The Radical project takes security seriously. If you discover a security vulnerability, memory safety defect, or sandbox escape within Radical's runtime or compiler, please report it responsibly.

### How to Report
- **Email**: Send a detailed report to `security@radical-lang.org`.
- **Do not** disclose security vulnerabilities via public GitHub issues, discussions, or pull requests until a patch has been coordinated.

### What to Include
1. Type of issue (e.g., buffer overflow in `buffer[T]`, unsafe pointer dereference escape, compiler injection via template literals).
2. Minimal, reproducible `.rad` source code triggering the defect.
3. Operating system, Python version, and hardware architecture (e.g., macOS Sonoma, Apple Silicon M3, Python 3.12).
4. Any potential remediation steps or suggested fixes.

### Response Timeline
- We will acknowledge receipt of your vulnerability report within 48 hours.
- A private patch will be prepared and verified against our automated test suites.
- A coordinated security release and public advisory will be issued upon patch verification.
