#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SC-Controller - Internationalization Support
"""

import os
import sys
import gettext
import ctypes
import ctypes.util
import logging

log = logging.getLogger("i18n")
# ══════════════════════════════════════════════════════════════════════
# CRITICAL: Set LANGUAGE env var IMMEDIATELY on module import
# GLib/GTK reads this at import time, so it must be set ASAP
# ══════════════════════════════════════════════════════════════════════
def _early_language_setup():
    """Set LANGUAGE env var if empty — must happen before GTK import"""
    import os
    
    # If LANGUAGE is empty string, GLib treats it as "no locale"
    if not os.environ.get('LANGUAGE'):
        # Try to get from LANG
        lang = os.environ.get('LANG', 'en_US.UTF-8')
        lang_code = lang.split('.')[0].split(':')[0]
        os.environ['LANGUAGE'] = lang_code
        # Don't log here — logging not initialized yet
        # print(f"[i18n early] Set LANGUAGE={lang_code} (was empty)")

_early_language_setup()
# ══════════════════════════════════════════════════════════════════════


APP_NAME = "sc-controller"

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
LOCALE_PATH = os.path.normpath(os.path.join(_THIS_DIR, "..", "locale"))

_translator = None


def _find_locale_path():
    for path in [LOCALE_PATH, "/usr/share/locale", "/usr/local/share/locale"]:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                if APP_NAME + ".mo" in files:
                    return path
    return LOCALE_PATH


def get_config_language():
    try:
        from scc.config import Config
        return Config().get('language', 'system') or 'system'
    except Exception:
        return 'system'


def _bind_libintl(locale_path, lang_code):
    """Call bindtextdomain via C so Gtk.Builder translates .glade strings."""
    libintl = None
    for name in ['libintl.so.8', 'libintl.so', 'libc.so.6', 'libc.so']:
        try:
            libintl = ctypes.CDLL(name)
            _ = libintl.bindtextdomain
            log.debug("i18n: libintl loaded from %s", name)
            break
        except (OSError, AttributeError):
            libintl = None

    if libintl is None:
        log.warning("i18n: could not load libintl — .glade strings may not be translated")
        return False

    path_bytes = locale_path.encode('utf-8')
    name_bytes = APP_NAME.encode('utf-8')

    try:
        result = libintl.bindtextdomain(name_bytes, path_bytes)
        libintl.textdomain(name_bytes)
        try:
            libintl.bind_textdomain_codeset(name_bytes, b'UTF-8')
        except Exception:
            pass
        log.debug("i18n: bindtextdomain('%s', '%s') = %s", APP_NAME, locale_path, result)
        return True
    except Exception as e:
        log.warning("i18n: bindtextdomain failed: %s", e)
        return False


def init_translations():
    """
    Initialize translation system. MUST be called before `import gi`.
    """
    global _translator

    lang = get_config_language()
    locale_path = _find_locale_path()

    log.debug("i18n: configured language = %r", lang)
    log.debug("i18n: locale path = %r", locale_path)
    log.debug("i18n: .mo exists = %s", os.path.exists(
        os.path.join(locale_path, 'pt_BR', 'LC_MESSAGES', APP_NAME + '.mo')))

    # ── 1. Set env vars before GTK loads ──────────────────────────────────
    if lang == 'system':
        # os.environ.get('LANGUAGE') may return '' (empty string) which
        # GLib treats as "no language set" — fall back to LANG in that case
        raw = os.environ.get('LANGUAGE') or os.environ.get('LANG', 'en_US')
        lang_code = raw.split(':')[0].split('.')[0]
        log.debug("i18n: using system language = %r", lang_code)
    else:
        lang_code = lang
        # Always set LANGUAGE (GLib reads this first) — never leave it empty
        os.environ['LANGUAGE'] = lang_code
        os.environ['LANG'] = lang_code + '.UTF-8'
        os.environ['LC_ALL'] = lang_code + '.UTF-8'
        os.environ['LC_MESSAGES'] = lang_code + '.UTF-8'
        log.debug("i18n: forced language = %r", lang_code)

    # If LANGUAGE is empty string, GLib ignores it — fix that now
    if not os.environ.get('LANGUAGE'):
        os.environ['LANGUAGE'] = lang_code
        log.debug("i18n: LANGUAGE was empty, set to %r", lang_code)

    log.debug("i18n: LANGUAGE=%r LANG=%r", os.environ.get('LANGUAGE'), os.environ.get('LANG'))

    # ── 2. Python gettext ──────────────────────────────────────────────────
    gettext.bindtextdomain(APP_NAME, locale_path)
    gettext.textdomain(APP_NAME)

    try:
        _translator = gettext.translation(
            APP_NAME, localedir=locale_path, languages=[lang_code])
        log.debug("i18n: Python gettext loaded, catalog size = %d",
                  len(_translator._catalog))
        # Quick smoke test
        test = _translator.gettext('Settings')
        log.debug("i18n: smoke test 'Settings' => %r", test)
    except FileNotFoundError as e:
        log.warning("i18n: .mo not found: %s — falling back to NullTranslations", e)
        _translator = gettext.NullTranslations()

    _translator.install()

    # ── 3. C libintl (for Gtk.Builder / .glade) ───────────────────────────
    ok = _bind_libintl(locale_path, lang_code)
    log.debug("i18n: libintl bind = %s", ok)

    return _translator.gettext


def patch_gtk_builder():
    """
    Patch Gtk.Builder so every instance automatically calls
    set_translation_domain(APP_NAME).

    Must be called after gi.require_version('Gtk','3.0') but before
    any code does `from gi.repository import Gtk` (i.e., before importing
    any scc.gui module).
    """
    try:
        from gi.repository import Gtk as _Gtk
    except ImportError:
        log.warning("i18n: could not import Gtk for patching")
        return

    _OrigBuilder = _Gtk.Builder
    _domain = APP_NAME

    class _PatchedBuilder(_OrigBuilder):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.set_translation_domain(_domain)
            log.debug("i18n: Builder() — set_translation_domain(%r)", _domain)

    _Gtk.Builder = _PatchedBuilder
    log.debug("i18n: Gtk.Builder patched")


def gettext_func(message):
    global _translator
    if _translator is None:
        init_translations()
    return _translator.gettext(message)


def ngettext_func(singular, plural, n):
    global _translator
    if _translator is None:
        init_translations()
    return _translator.ngettext(singular, plural, n)


def pgettext_func(context, message):
    combined = "%s\x04%s" % (context, message)
    result = gettext_func(combined)
    return message if result == combined else result


_ = gettext_func
ngettext = ngettext_func
pgettext = pgettext_func


def make_dialog(parent, dtype, title, secondary=None, buttons='yes_no'):
    """
    Cria um MessageDialog com botões traduzidos explicitamente.
    Mantém os mesmos response IDs do GTK para compatibilidade.
    
    buttons: 'yes_no' | 'ok_cancel' | 'ok'
    Returns: Gtk.MessageDialog
    """
    from gi.repository import Gtk

    type_map = {
        'question': Gtk.MessageType.QUESTION,
        'warning':  Gtk.MessageType.WARNING,
        'error':    Gtk.MessageType.ERROR,
        'info':     Gtk.MessageType.INFO,
    }

    d = Gtk.MessageDialog(
        parent=parent,
        flags=Gtk.DialogFlags.MODAL,
        type=type_map.get(dtype, Gtk.MessageType.QUESTION),
        buttons=Gtk.ButtonsType.NONE,
        message_format=title,
    )
    if secondary:
        d.format_secondary_text(secondary)

    if buttons == 'yes_no':
        d.add_button(_("No"),  -9)   # Gtk.ResponseType.NO
        d.add_button(_("Yes"), -8)   # Gtk.ResponseType.YES
        d.set_default_response(-8)
    elif buttons == 'ok_cancel':
        d.add_button(_("Cancel"), -6)  # Gtk.ResponseType.CANCEL
        d.add_button(_("OK"),     -5)  # Gtk.ResponseType.OK
        d.set_default_response(-5)
    elif buttons == 'ok':
        d.add_button(_("OK"), -5)
        d.set_default_response(-5)

    return d
