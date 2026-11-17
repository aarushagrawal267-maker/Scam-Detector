"""AI Scam Message Detector.

Checks a message (SMS / WhatsApp text, or text read from a screenshot) and returns:
  - a verdict: SCAM / SUSPICIOUS / LIKELY SAFE (never a guarantee),
  - the likely scam type,
  - the red flags found, in plain English or Hindi,
  - what to do next.

Main entry point: ``scam_detector.detector.check_message``.
"""

__version__ = "0.1.0"
