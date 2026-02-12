"""
Utility functions for companies app
"""
from django.core.signing import Signer, BadSignature, TimestampSigner, SignatureExpired
from django.conf import settings
import hashlib
import hmac


def format_riyadh_datetime(dt):
    """Format datetime in Riyadh timezone"""
    if not dt:
        return '-'
    from django.utils import timezone
    from pytz import timezone as tz
    riyadh_tz = tz('Asia/Riyadh')
    if timezone.is_aware(dt):
        dt = dt.astimezone(riyadh_tz)
    else:
        dt = timezone.make_aware(dt, riyadh_tz)
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def format_arabic_datetime(dt):
    """Format datetime in Arabic-friendly format"""
    if not dt:
        return '-'
    from django.utils import timezone
    from pytz import timezone as tz
    riyadh_tz = tz('Asia/Riyadh')
    if timezone.is_aware(dt):
        dt = dt.astimezone(riyadh_tz)
    else:
        dt = timezone.make_aware(dt, riyadh_tz)
    return dt.strftime('%Y-%m-%d %H:%M')


def encrypt_slug(slug, salt=None):
    """
    Sign a slug using Django's signing mechanism.

    The output of ``Signer.sign`` is already safe to use in URLs, so we don't
    do any manual character replacements. This keeps the value reversible and
    avoids corrupting the signature.
    """
    if not slug:
        return None

    # Use a custom salt for additional security
    if salt is None:
        salt = getattr(settings, 'SLUG_SIGNING_SALT', 'dawerha-slug-signing-secure-2025')

    signer = Signer(salt=salt)
    try:
        return signer.sign(slug)
    except Exception:
        return None


def decrypt_slug(encrypted_token, salt=None):
    """
    Decrypt a signed slug token.

    Supports both the **new** format (direct ``Signer.sign`` output) and the
    **old** format that replaced ``:`` with ``-`` and ``/`` with ``_``.

    Returns the original slug or ``None`` if the signature is invalid.
    """
    if not encrypted_token:
        return None

    # Use the same salt
    if salt is None:
        salt = getattr(settings, 'SLUG_SIGNING_SALT', 'dawerha-slug-signing-secure-2025')

    signer = Signer(salt=salt)

    # First try the new (direct) format
    try:
        return signer.unsign(encrypted_token)
    except BadSignature:
        # Backwards-compatibility: try the old format that replaced characters
        try:
            legacy_token = encrypted_token.replace('-', ':').replace('_', '/')
            return signer.unsign(legacy_token)
        except BadSignature:
            return None
    except Exception:
        return None


def generate_secure_token(slug, max_age=None):
    """
    Generate a secure token for a slug with optional expiration.

    ``max_age`` is only used when *verifying* the token; here we just sign it.
    """
    if not slug:
        return None

    salt = getattr(settings, 'SLUG_SIGNING_SALT', 'dawerha-slug-signing-secure-2025')

    try:
        if max_age:
            # Use TimestampSigner so we can enforce expiration on verify
            timestamp_signer = TimestampSigner(salt=salt)
            token = timestamp_signer.sign(slug)
        else:
            signer = Signer(salt=salt)
            token = signer.sign(slug)
        return token
    except Exception:
        return None


def verify_secure_token(token, max_age=None):
    """
    Verify and decrypt a secure token.

    Returns the slug or ``None`` if invalid/expired.
    """
    if not token:
        return None

    salt = getattr(settings, 'SLUG_SIGNING_SALT', 'dawerha-slug-signing-secure-2025')

    try:
        if max_age:
            timestamp_signer = TimestampSigner(salt=salt)
            try:
                # Try new format first
                slug = timestamp_signer.unsign(token, max_age=max_age)
                return slug
            except SignatureExpired:
                return None
            except BadSignature:
                # Legacy format: reverse replacements then try again
                try:
                    legacy_token = token.replace('-', ':').replace('_', '/')
                    slug = timestamp_signer.unsign(legacy_token, max_age=max_age)
                    return slug
                except (BadSignature, SignatureExpired):
                    return None
        else:
            signer = Signer(salt=salt)
            try:
                # New format
                slug = signer.unsign(token)
                return slug
            except BadSignature:
                # Legacy format
                try:
                    legacy_token = token.replace('-', ':').replace('_', '/')
                    slug = signer.unsign(legacy_token)
                    return slug
                except BadSignature:
                    return None
    except Exception:
        return None
