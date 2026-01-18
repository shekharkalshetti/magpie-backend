"""
Policy constants and enums.
"""

import enum


class PolicySeverity(str, enum.Enum):
    """Severity levels for policy sections."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PolicyCategoryType(str, enum.Enum):
    """Types of policy categories."""

    CONTENT_POLICY = "content-policy"
    FACTUALITY = "factuality"
    SECURITY = "security"


# Default policy configuration template
DEFAULT_POLICY_CONFIG = {
    "categories": [
        {
            "id": "content-policy",
            "name": "Content Policy Compliance",
            "enabled": True,
            "sections": [
                {
                    "id": "harmful-content",
                    "title": "Harmful Content Detection",
                    "severity": "critical",
                    "description": "Detects and blocks violence, illegal activities, and dangerous instructions.",
                    "policy_text": "Content must not contain instructions for violence, illegal activities, or dangerous behavior. Flag content depicting graphic violence or encouraging harm.",
                    "enabled": True,
                    "options": [
                        {"id": "graphic-violence",
                            "label": "Graphic Violence Detection", "enabled": True},
                        {"id": "illegal-activity",
                            "label": "Illegal Activity Instructions", "enabled": True},
                        {"id": "weapon-explosive",
                            "label": "Weapon/Explosive Instructions", "enabled": True},
                        {"id": "encouragement-harm",
                            "label": "Encouragement of Harm", "enabled": True},
                    ],
                },
                {
                    "id": "hate-speech",
                    "title": "Hate Speech & Discrimination",
                    "severity": "high",
                    "description": "Detects hate speech, slurs, and discriminatory content.",
                    "policy_text": "Content must not contain hate speech, slurs, or discriminatory language targeting protected groups. Monitor for dehumanizing language.",
                    "enabled": True,
                    "options": [
                        {"id": "slur-detection",
                            "label": "Slur Detection", "enabled": True},
                        {"id": "discriminatory-language",
                            "label": "Discriminatory Language", "enabled": True},
                        {"id": "dehumanizing-language",
                            "label": "Dehumanizing Language", "enabled": True},
                        {"id": "targeted-harassment",
                            "label": "Targeted Harassment", "enabled": True},
                    ],
                },
                {
                    "id": "sexual-content",
                    "title": "Sexual Content & CSAM Prevention",
                    "severity": "critical",
                    "description": "Detects sexual content and child safety risks.",
                    "policy_text": "Block explicit sexual content and any content involving minors. Zero tolerance for CSAM or child exploitation material.",
                    "enabled": True,
                    "options": [
                        {"id": "csam-prevention",
                            "label": "CSAM/Child Safety Prevention", "enabled": True},
                        {"id": "explicit-sexual",
                            "label": "Explicit Sexual Content", "enabled": True},
                        {"id": "minor-exploitation",
                            "label": "Minor Exploitation Attempts", "enabled": True},
                        {"id": "grooming-behavior",
                            "label": "Grooming Behavior Detection", "enabled": True},
                    ],
                },
                {
                    "id": "self-harm",
                    "title": "Self-Harm & Suicide Prevention",
                    "severity": "critical",
                    "description": "Detects content promoting self-harm or suicide.",
                    "policy_text": "Flag content promoting or instructing self-harm, suicide, or eating disorders. Provide mental health resources.",
                    "enabled": True,
                    "options": [
                        {"id": "suicide-content",
                            "label": "Suicide-Related Content", "enabled": True},
                        {"id": "self-harm-promotion",
                            "label": "Self-Harm Promotion", "enabled": True},
                        {"id": "eating-disorder",
                            "label": "Eating Disorder Glorification", "enabled": True},
                        {"id": "mental-health-crisis",
                            "label": "Mental Health Crisis Signs", "enabled": True},
                    ],
                },
                {
                    "id": "harassment",
                    "title": "Harassment & Bullying",
                    "severity": "high",
                    "description": "Detects harassment, cyberbullying, and abusive behavior.",
                    "policy_text": "Block targeted harassment, bullying, doxxing, and coordinated abuse. Include context from conversations.",
                    "enabled": True,
                    "options": [
                        {"id": "cyberbullying",
                            "label": "Cyberbullying Detection", "enabled": True},
                        {"id": "doxxing", "label": "Doxxing & Privacy Violations",
                            "enabled": True},
                        {"id": "coordinated-abuse",
                            "label": "Coordinated Abuse", "enabled": True},
                        {"id": "threats-intimidation",
                            "label": "Threats & Intimidation", "enabled": True},
                    ],
                },
                {
                    "id": "spam-manipulation",
                    "title": "Spam & Manipulation",
                    "severity": "medium",
                    "description": "Detects spam, scams, and manipulative content.",
                    "policy_text": "Flag spam, scam content, phishing, and manipulative schemes. Include repetition and pattern analysis.",
                    "enabled": True,
                    "options": [
                        {"id": "spam-repetitive",
                            "label": "Spam & Repetitive Content", "enabled": True},
                        {"id": "phishing", "label": "Phishing Attempts",
                            "enabled": True},
                        {"id": "scam-fraud", "label": "Scam & Fraud", "enabled": True},
                        {"id": "manipulative-behavior",
                            "label": "Manipulative Behavior", "enabled": True},
                    ],
                },
            ],
        },
        {
            "id": "factuality",
            "name": "Factuality & Truthfulness",
            "enabled": True,
            "sections": [
                {
                    "id": "hallucination",
                    "title": "Hallucination Detection",
                    "severity": "high",
                    "description": "Detects when AI generates false or fabricated information.",
                    "policy_text": "Identify responses that contain completely fabricated facts or false claims presented as true.",
                    "enabled": True,
                    "options": [
                        {"id": "fabricated-facts",
                            "label": "Completely Fabricated Facts", "enabled": True},
                        {"id": "false-claims", "label": "False Claims", "enabled": True},
                        {"id": "internal-contradictions",
                            "label": "Internal Contradictions", "enabled": True},
                        {"id": "unwarranted-confidence",
                            "label": "Unwarranted Confidence", "enabled": True},
                    ],
                },
                {
                    "id": "factual-accuracy",
                    "title": "Factual Accuracy Verification",
                    "severity": "high",
                    "description": "Verifies accuracy of factual claims and statements.",
                    "policy_text": "Cross-reference factual claims against reliable sources. Flag unverified or contradicted statements.",
                    "enabled": True,
                    "options": [
                        {"id": "source-verification",
                            "label": "Source Verification", "enabled": True},
                        {"id": "date-timeline",
                            "label": "Date & Timeline Accuracy", "enabled": True},
                        {"id": "statistical-claims",
                            "label": "Statistical Claims Verification", "enabled": True},
                        {"id": "quote-accuracy",
                            "label": "Quote Accuracy Check", "enabled": True},
                    ],
                },
                {
                    "id": "misinformation",
                    "title": "Misinformation & Disinformation",
                    "severity": "high",
                    "description": "Detects false information and deliberate disinformation campaigns.",
                    "policy_text": "Identify debunked claims, false narratives, and coordinated disinformation. Flag context manipulation.",
                    "enabled": True,
                    "options": [
                        {"id": "debunked-claims",
                            "label": "Debunked Claims", "enabled": True},
                        {"id": "false-narratives",
                            "label": "False Narratives", "enabled": True},
                        {"id": "coordinated-disinfo",
                            "label": "Coordinated Disinformation", "enabled": True},
                        {"id": "context-manipulation",
                            "label": "Context Manipulation", "enabled": True},
                    ],
                },
                {
                    "id": "medical-claims",
                    "title": "Medical/Health Claim Verification",
                    "severity": "critical",
                    "description": "Validates medical and health-related claims for accuracy.",
                    "policy_text": "Verify medical claims against peer-reviewed research and guidelines. Flag dangerous health misinformation.",
                    "enabled": True,
                    "options": [
                        {"id": "treatment-cure",
                            "label": "Treatment/Cure Claims", "enabled": True},
                        {"id": "vaccine-safety",
                            "label": "Vaccine Safety Claims", "enabled": True},
                        {"id": "dangerous-medical",
                            "label": "Dangerous Medical Advice", "enabled": True},
                        {"id": "medication-info",
                            "label": "Medication Information", "enabled": True},
                    ],
                },
                {
                    "id": "financial-info",
                    "title": "Financial Information Accuracy",
                    "severity": "high",
                    "description": "Ensures accuracy of financial advice and market information.",
                    "policy_text": "Verify financial claims, stock data, and investment advice. Require disclaimers for non-professional advice.",
                    "enabled": True,
                    "options": [
                        {"id": "stock-data", "label": "Stock Data Accuracy",
                            "enabled": True},
                        {"id": "investment-advice",
                            "label": "Investment Advice", "enabled": True},
                        {"id": "financial-forecasts",
                            "label": "Financial Forecasts", "enabled": True},
                        {"id": "professional-disclaimer",
                            "label": "Professional Disclaimer Check", "enabled": True},
                    ],
                },
            ],
        },
        {
            "id": "security",
            "name": "Security & Safety",
            "enabled": True,
            "sections": [
                {
                    "id": "jailbreak",
                    "title": "Jailbreak Attempt Detection",
                    "severity": "high",
                    "description": "Detects attempts to circumvent safety guidelines.",
                    "policy_text": "Identify sophisticated prompt engineering and jailbreak attempts designed to bypass content filters.",
                    "enabled": True,
                    "options": [
                        {"id": "prompt-engineering",
                            "label": "Prompt Engineering Attempts", "enabled": True},
                        {"id": "instruction-override",
                            "label": "Instruction Override Attempts", "enabled": True},
                        {"id": "context-confusion",
                            "label": "Context Confusion Tactics", "enabled": True},
                        {"id": "roleplay-abuse",
                            "label": "Role-Play Abuse", "enabled": True},
                    ],
                },
                {
                    "id": "prompt-injection",
                    "title": "Prompt Injection Vulnerabilities",
                    "severity": "high",
                    "description": "Detects prompt injection and manipulation attacks.",
                    "policy_text": "Flag attempts to inject malicious instructions or change system behavior through user input.",
                    "enabled": True,
                    "options": [
                        {"id": "instruction-injection",
                            "label": "Instruction Injection", "enabled": True},
                        {"id": "system-prompt-leakage",
                            "label": "System Prompt Leakage", "enabled": True},
                        {"id": "function-calling-abuse",
                            "label": "Function Calling Abuse", "enabled": True},
                        {"id": "data-extraction",
                            "label": "Data Extraction Attempts", "enabled": True},
                    ],
                },
                {
                    "id": "adversarial",
                    "title": "Adversarial Attack Resistance",
                    "severity": "high",
                    "description": "Resists adversarial examples and manipulation tactics.",
                    "policy_text": "Detect adversarial inputs designed to confuse or exploit the system. Monitor for pattern attacks.",
                    "enabled": True,
                    "options": [
                        {"id": "adversarial-examples",
                            "label": "Adversarial Examples", "enabled": True},
                        {"id": "evasion-attacks",
                            "label": "Evasion Attacks", "enabled": True},
                        {"id": "data-poisoning",
                            "label": "Data Poisoning Attempts", "enabled": True},
                        {"id": "trojan-pattern",
                            "label": "Trojan Pattern Detection", "enabled": True},
                    ],
                },
                {
                    "id": "code-security",
                    "title": "Code Security Vulnerabilities",
                    "severity": "high",
                    "description": "Detects insecure code and security vulnerabilities.",
                    "policy_text": "Flag code with SQL injection, buffer overflows, insecure dependencies, and other known vulnerabilities.",
                    "enabled": True,
                    "options": [
                        {"id": "sql-injection",
                            "label": "SQL Injection Patterns", "enabled": True},
                        {"id": "buffer-overflow",
                            "label": "Buffer Overflow Risks", "enabled": True},
                        {"id": "insecure-dependencies",
                            "label": "Insecure Dependencies", "enabled": True},
                        {"id": "hardcoded-secrets",
                            "label": "Hardcoded Secrets", "enabled": True},
                    ],
                },
                {
                    "id": "credential-pii",
                    "title": "Credential & PII Leakage Prevention",
                    "severity": "critical",
                    "description": "Prevents exposure of credentials and personally identifiable information.",
                    "policy_text": "Block exposure of SSNs, credit card numbers, API keys, passwords, and sensitive personal data.",
                    "enabled": True,
                    "options": [
                        {"id": "ssn-tax-id", "label": "SSN/Tax ID Detection",
                            "enabled": True},
                        {"id": "payment-card",
                            "label": "Payment Card Detection", "enabled": True},
                        {"id": "api-keys-tokens",
                            "label": "API Keys & Tokens", "enabled": True},
                        {"id": "personal-data",
                            "label": "Personal Data (Email, Phone)", "enabled": True},
                    ],
                },
            ],
        },
    ]
}
