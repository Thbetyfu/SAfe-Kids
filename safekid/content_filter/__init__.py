"""
SafeKid Flash — Content Filter Package
========================================
Modul ini menyediakan content filtering untuk SafeKid Flash:

  dns_filter.py      → Ganti DNS sistem ke safe DNS server
  blocklist_manager.py → Download & kelola daftar domain blokir
  proxy_config.py    → Generate konfigurasi Squid proxy
  safe_search.py     → Paksa safe search di Google/YouTube/Bing

Usage (Linux only):
    from safekid.content_filter import ContentFilterManager
    
    cf = ContentFilterManager()
    cf.enable_all()
"""

from .filter_manager import ContentFilterManager

__all__ = ["ContentFilterManager"]
