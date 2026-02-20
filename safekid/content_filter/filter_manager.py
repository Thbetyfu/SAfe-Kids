"""
SafeKid Flash — Content Filter Manager
=========================================
Facade yang mengintegrasikan semua komponen filtering:
  • DNSFilter        — Ganti DNS sistem
  • BlocklistManager — Kelola daftar domain blokir
  • ProxyConfig      — Konfigurasi Squid proxy (coming soon)
  • SafeSearch       — Paksa safe search

Usage (Linux, run as root):
    from safekid.content_filter import ContentFilterManager

    cf = ContentFilterManager(age=9)
    cf.enable_all()
    print(cf.status())
"""

import logging
import platform
from typing import Optional

from .dns_filter import DNSFilter, DNSProvider
from .blocklist_manager import BlocklistManager, BlockCategory

logger = logging.getLogger("safekid.content_filter")
IS_LINUX = platform.system() == "Linux"


class ContentFilterManager:
    """
    One-stop manager untuk semua content filtering.

    Contoh penggunaan:
        # Setup untuk anak usia 8 tahun
        cf = ContentFilterManager(age=8, dns_provider=DNSProvider.OPENDNS_FAMILY)
        cf.setup()            # Download blocklists, configure DNS
        cf.enable_all()       # Enable everything
        
        # Check status
        print(cf.status())
        
        # Disable (parent override)
        cf.disable_all()
    """

    # Age-based presets: which categories to block
    AGE_PRESETS = {
        range(0,  7): [BlockCategory.ADULT, BlockCategory.GAMBLING, BlockCategory.VIOLENCE, BlockCategory.MALWARE],
        range(7, 13): [BlockCategory.ADULT, BlockCategory.GAMBLING, BlockCategory.VIOLENCE, BlockCategory.MALWARE],
        range(13,18): [BlockCategory.ADULT, BlockCategory.GAMBLING, BlockCategory.MALWARE],
        range(18,99): [BlockCategory.MALWARE],
    }

    def __init__(
        self,
        age: int              = 0,
        dns_provider: DNSProvider = DNSProvider.OPENDNS_FAMILY,
        dry_run: bool         = not IS_LINUX,
    ):
        self.age        = age
        self.dry_run    = dry_run

        self.dns_filter = DNSFilter(provider=dns_provider, dry_run=dry_run)
        self.blocklist  = BlocklistManager()

        self._dns_enabled       = False
        self._blocklist_enabled = False

        if not IS_LINUX and not dry_run:
            logger.warning("Content filtering is Linux-only. Running in dry_run mode.")
            self.dry_run = True

    # ── Age preset ───────────────────────────────

    def get_categories_for_age(self) -> list:
        """Return recommended block categories for current age."""
        for age_range, cats in self.AGE_PRESETS.items():
            if self.age in age_range:
                return cats
        return [BlockCategory.ADULT, BlockCategory.MALWARE]  # default

    # ── Setup ────────────────────────────────────

    def setup(self, download_blocklists: bool = True) -> bool:
        """
        Initial setup: download blocklists based on age group.
        Does NOT enable filtering yet — call enable_all() after.
        """
        logger.info(f"Setting up content filter for age {self.age}...")
        categories = self.get_categories_for_age()
        logger.info(f"Categories for age {self.age}: {[c.value for c in categories]}")

        if download_blocklists:
            if self.dry_run:
                logger.info("[DRY RUN] Would download blocklists for: "
                            f"{[c.value for c in categories]}")
                return True
            results = self.blocklist.update_all(categories=categories)
            failed  = [k for k, v in results.items() if not v]
            if failed:
                logger.warning(f"Some downloads failed: {failed}")
            total = self.blocklist.build_combined()
            logger.info(f"Setup complete: {total:,} domains in blocklist")

        return True

    # ── Enable / Disable ──────────────────────────

    def enable_dns(self) -> bool:
        ok = self.dns_filter.enable()
        self._dns_enabled = ok
        return ok

    def disable_dns(self) -> bool:
        ok = self.dns_filter.disable()
        self._dns_enabled = not ok
        return ok

    def enable_all(self) -> dict:
        """Enable all available content filters."""
        results = {
            "dns":       self.enable_dns(),
            "blocklist": True,  # Blocklist is passive (used by Squid/pi-hole)
        }
        logger.info(f"Content filter enabled: {results}")
        return results

    def disable_all(self) -> dict:
        """Disable all content filters (parent override)."""
        results = {
            "dns": self.disable_dns(),
        }
        logger.info(f"Content filter disabled: {results}")
        return results

    # ── Lookup ────────────────────────────────────

    def is_domain_blocked(self, domain: str) -> bool:
        """Check if a domain would be blocked."""
        return self.blocklist.is_blocked(domain)

    def block_domain(self, domain: str) -> bool:
        """Add domain to custom blocklist."""
        return self.blocklist.add_domain(domain)

    def unblock_domain(self, domain: str) -> bool:
        """Remove domain from custom blocklist."""
        return self.blocklist.remove_domain(domain)

    # ── Status ────────────────────────────────────

    def status(self) -> dict:
        return {
            "age":               self.age,
            "platform":          platform.system(),
            "dry_run":           self.dry_run,
            "linux_only":        not IS_LINUX,
            "dns":               self.dns_filter.status(),
            "blocklist": {
                "total_blocked": self.blocklist.total_blocked,
                "sources":       len(self.blocklist.sources),
            },
            "age_categories":    [c.value for c in self.get_categories_for_age()],
        }

    def __repr__(self):
        return (f"ContentFilterManager(age={self.age}, "
                f"dns={self._dns_enabled}, "
                f"blocklist={self.blocklist.total_blocked:,})")
