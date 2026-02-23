#!/usr/bin/env python3
import os
import signal
import sys


def main() -> None:
	def sigint(*a):
		print("\n*break*")
		sys.exit(0)

	signal.signal(signal.SIGINT, sigint)

	# ── i18n: ANTES de importar GTK ──────────────────────────────────────
	from scc.i18n import init_translations
	init_translations()
	# ─────────────────────────────────────────────────────────────────────

	import gi
	gi.require_version('Gtk', '3.0')
	gi.require_version('GdkX11', '3.0')
	gi.require_version('Rsvg', '2.0')

	# ── i18n: Patch GTK Builder ──────────────────────────────────────────
	from scc.i18n import patch_gtk_builder
	patch_gtk_builder()
	# ─────────────────────────────────────────────────────────────────────

	from scc.paths import get_share_path
	from scc.tools import init_logging
	init_logging()

	from gi.repository import Gtk, GObject
	glades = os.path.join(get_share_path(), "glade")
	images = os.path.join(get_share_path(), "images")
	if Gtk.IconTheme.get_default():
		Gtk.IconTheme.get_default().append_search_path(images)

	from scc.gui.app import App
	App(glades, images).run(sys.argv)

if __name__ == "__main__":
	main()
