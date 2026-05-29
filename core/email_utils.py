"""
ZeptoMail API Email Utility for Sneaky Klean

Provides API-based email sending functionality as an alternative to SMTP.
"""

import base64
import logging
import mimetypes
from collections.abc import Sequence
from email.utils import parseaddr

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class ZeptoMailAPIError(Exception):
    """Exception raised for ZeptoMail API errors."""
    pass


def _parse_recipients(recipients: str | Sequence[str], quiet: bool = True) -> list[dict]:
    """Parse and normalize recipients into ZeptoMail format."""
    # Normalize recipients to list
    recipient_list = list(recipients) if isinstance(recipients, (list, tuple, set)) else [recipients]

    # Parse and validate each recipient
    to_list = []
    for raw in recipient_list:
        display_name, email_addr = parseaddr(str(raw))
        if not email_addr:
            msg = f"Invalid recipient format for ZeptoMail: {raw!r}"
            logger.error(msg)
            if not quiet:
                raise ValueError(msg)
            continue

        to_list.append({
            "email_address": {
                "address": email_addr,
                "name": display_name or email_addr,
            },
        })

    if not to_list:
        msg = "ZeptoMail send skipped: no valid recipients"
        logger.error(msg)
        if not quiet:
            raise ValueError(msg)

    return to_list


def _parse_from_address(quiet: bool = True) -> dict:
    """Parse and validate the from address."""
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
    from_name, from_addr = parseaddr(from_email)
    
    if not from_addr:
        msg = f"Invalid DEFAULT_FROM_EMAIL for ZeptoMail: {from_email!r}"
        logger.error(msg)
        if not quiet:
            raise ValueError(msg)
        return {}

    return {
        "address": from_addr,
        "name": from_name or from_addr,
    }


def _build_attachments(attachments: Sequence | None) -> list[dict]:
    """Build ZeptoMail attachment objects."""
    api_attachments: list[dict] = []
    if not attachments:
        return api_attachments

    for att in attachments:
        # Expected: (filename, content_bytes, mimetype?)
        filename = None
        content = None
        mimetype = None

        if isinstance(att, (list, tuple)) and len(att) in (2, 3):
            filename = att[0]
            content = att[1]
            mimetype = att[2] if len(att) == 3 else None
        else:
            logger.warning("Unsupported attachment type for ZeptoMail: %r", att)
            continue

        if not mimetype:
            mimetype, _ = mimetypes.guess_type(filename)
        mimetype = mimetype or "application/octet-stream"

        if isinstance(content, str):
            content = content.encode("utf-8")

        api_attachments.append({
            "name": filename,
            "mime_type": mimetype,
            "content": base64.b64encode(content).decode("ascii"),
        })

    return api_attachments


def _prepare_body_content(body_text: str, body_html: str) -> tuple[str, str]:
    """Prepare and normalize email body content."""
    if not body_html and body_text:
        body_html = f"<p>{body_text}</p>"

    if not body_text and body_html:
        # Crude text fallback
        body_text = body_html.replace("<br>", "\n").replace("<br/>", "\n")

    return body_text, body_html


def _get_api_config(quiet: bool = True) -> tuple[str, str, dict] | tuple[None, None, None]:
    """Get ZeptoMail API configuration."""
    api_key = getattr(settings, "ZEPTO_API_KEY", None)
    base_url = getattr(settings, "ZEPTO_API_BASE_URL", "").rstrip("/")

    if not api_key or not base_url:
        msg = "ZeptoMail API not configured (ZEPTO_API_KEY / ZEPTO_API_BASE_URL missing)"
        logger.warning(msg)
        if not quiet:
            raise ZeptoMailAPIError(msg)
        return None, None, None

    url = f"{base_url}/email"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Zoho-enczapikey {api_key}",
        "Content-Type": "application/json",
    }

    return url, api_key, headers


def _send_api_request(url: str, headers: dict, payload: dict, subject: str, to_list: list, quiet: bool = True):
    """Send the actual API request to ZeptoMail."""
    logger.debug("ZeptoMail request payload: %r", payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.status_code >= 400:
            logger.error(
                "ZeptoMail API error: %s %s (subject=%r)",
                resp.status_code,
                resp.text,
                subject,
            )
            if not quiet:
                raise ZeptoMailAPIError(
                    f"ZeptoMail API error {resp.status_code}: {resp.text}",
                )
            return None

        try:
            data = resp.json()
        except ValueError:
            data = resp.text

        logger.info(
            "ZeptoMail email sent to %s (subject=%r)",
            [r["email_address"]["address"] for r in to_list],
            subject,
        )
        return data

    except requests.exceptions.RequestException as exc:
        logger.exception("Error sending email via ZeptoMail API: %s", exc)
        if not quiet:
            raise
        return None


def send_zeptomail_email(
    recipients: str | Sequence[str],
    subject: str,
    body_text: str = "",
    body_html: str = "",
    attachments: Sequence | None = None,
    quiet: bool = True,
):
    """
    Send an email via ZeptoMail HTTP API.

    Args:
        recipients: Single email or list of emails
            - "user@example.com"
            - "Full Name <user@example.com>"
            - ["a@example.com", "B Name <b@example.com>", ...]
        subject: Email subject line
        body_text: Plain text email body
        body_html: HTML email body
        attachments: List of (filename, content_bytes, mimetype?)
            e.g., [("invoice.pdf", pdf_bytes, "application/pdf")]
        quiet: If True, log errors but don't raise exceptions

    Returns:
        API response data or None if failed
    """

    # Parse recipients
    to_list = _parse_recipients(recipients, quiet)
    if not to_list:
        return None

    # Prepare body content
    body_text, body_html = _prepare_body_content(body_text, body_html)

    # Get API configuration
    url, api_key, headers = _get_api_config(quiet)
    if not url:
        return None

    # Parse from address
    from_obj = _parse_from_address(quiet)
    if not from_obj:
        return None

    # Build attachments
    api_attachments = _build_attachments(attachments)

    # Build payload
    payload = {
        "from": from_obj,
        "to": to_list,
        "subject": subject or "",
        "textbody": body_text or "",
        "htmlbody": body_html or "",
    }

    if api_attachments:
        payload["attachments"] = api_attachments

    # Send request
    return _send_api_request(url, headers, payload, subject, to_list, quiet)


def send_email(
    recipient,
    subject="",
    body_text="",
    body_html="",
    attachments=None,
    quiet=True
):
    """
    Simplified email sending function.
    
    Args:
        recipient: Email address or list of email addresses
        subject: Email subject
        body_text: Plain text body
        body_html: HTML body (will generate from text if not provided)
        attachments: Optional list of attachments
        quiet: If True, suppress exceptions and log errors instead
    
    Returns:
        API response or None
    """
    if not body_html and body_text:
        body_html = f"<p>{body_text}</p>"

    return send_zeptomail_email(
        recipients=recipient,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        attachments=attachments,
        quiet=quiet,
    )
