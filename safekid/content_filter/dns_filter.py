"""
SafeKid Flash — DNS Filter
============================
Mengganti konfigurasi DNS sistem ke layanan DNS aman:
• OpenDNS FamilyShield (208.67.222.123 / 208.67.220.123)
• Cloudflare Family (1.1.1.3 / 1.0.0.3)
• CleanBrowsing Family (185.228.168.168 / 185.228.169.168)

Berjalan di Linux — membutuhkan root/sudo untuk menulis /etc/resolv.conf.

Konsep kerja:
  1. Backup /etc/resolv.conf ke /etc/resolv.conf.safekid.bak
  2. Tulis nameserver baru ke /etc/resolv.conf
  3. (Opsional) Lock file agar tidak bisa diubah NetworkManager

Untuk mengembalikan DNS asli:
  cf_dns = DNSFilter()
  cf_dns.disable()
"""

import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("safekid.dns_filter")

RESOLV_CONF     = Path("/etc/resolv.conf")
RESOLV_BACKUP   = Path("/etc/resolv.conf.safekid.bak")
RESOLV_ORIGINAL = Path("/etc/resolv.conf.safekid.original")


# ────────────────────────────────────────────────────
#  DNS Provider Presets
# ────────────────────────────────────────────────────

class DNSProvider(Enum):
    OPENDNS_FAMILY      = "opendns_family"
    CLOUDFLARE_FAMILY   = "cloudflare_family"
    CLEANBROWSING_FAMILY= "cleanbrowsing_family"
    QUAD9               = "quad9"
    CUSTOM              = "custom"


@dataclass
class DNSConfig:
    """Configuration for a DNS filter provider."""
    name:        str
    primary:     str
    secondary:   str
    description: str
    blocks:      List[str] = field(default_factory=list)

    def to_resolv_conf(self, search_domain: str = "") -> str:
        lines = [
            "# SafeKid Flash — Managed DNS Configuration",
            "# DO NOT EDIT — managed by safekid content filter",
            f"# Provider: {self.name}",
            "",
        ]
        if search_domain:
            lines.append(f"search {search_domain}")
        lines.append(f"nameserver {self.primary}")
        lines.append(f"nameserver {self.secondary}")
        return "\n".join(lines) + "\n"


# ── Preset providers ─────────────────────────────────
DNS_PROVIDERS = {
    DNSProvider.OPENDNS_FAMILY: DNSConfig(
        name="OpenDNS FamilyShield",
        primary="208.67.222.123",
        secondary="208.67.220.123",
        description="Blocks adult content, phishing, malware",
        blocks=["adult", "phishing", "malware"],
    ),
    DNSProvider.CLOUDFLARE_FAMILY: DNSConfig(
        name="Cloudflare for Families",
        primary="1.1.1.3",
        secondary="1.0.0.3",
        description="Blocks malware and adult content",
        blocks=["adult", "malware"],
    ),
    DNSProvider.CLEANBROWSING_FAMILY: DNSConfig(
        name="CleanBrowsing Family Filter",
        primary="185.228.168.168",
        secondary="185.228.169.168",
        description="Strict family filter — blocks adult, VPN bypass",
        blocks=["adult", "malware", "phishing", "vpn_bypass"],
    ),
    DNSProvider.QUAD9: DNSConfig(
        name="Quad9",
        primary="9.9.9.9",
        secondary="149.112.112.112",
        description="Blocks malware and phishing only",
        blocks=["malware", "phishing"],
    ),
}


# ────────────────────────────────────────────────────
#  DNS Filter
# ────────────────────────────────────────────────────

class DNSFilter:
    """
    Mengelola substitusi DNS sistem untuk content filtering.

    Contoh penggunaan (harus root):
        filter = DNSFilter(provider=DNSProvider.OPENDNS_FAMILY)
        filter.enable()
        # ... anak bermain ...
        filter.disable()
    """

    def __init__(
        self,
        provider: DNSProvider = DNSProvider.OPENDNS_FAMILY,
        custom_primary: str   = "",
        custom_secondary: str = "",
        dry_run: bool         = False,
    ):
        self.provider         = provider
        self.custom_primary   = custom_primary
        self.custom_secondary = custom_secondary
        self.dry_run          = dry_run   # If True, print changes but don't write
        self._active          = False

        if provider == DNSProvider.CUSTOM:
            self._config = DNSConfig(
                name="Custom",
                primary=custom_primary or "8.8.8.8",
                secondary=custom_secondary or "8.8.4.4",
                description="Custom DNS server",
            )
        else:
            self._config = DNS_PROVIDERS[provider]

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def config(self) -> DNSConfig:
        return self._config

    def enable(self) -> bool:
        """
        Aktifkan DNS filtering.
        Returns True jika berhasil.
        Membutuhkan root privileges.
        """
        if not self._check_root():
            logger.error("DNS filter requires root privileges. Run with sudo.")
            return False

        try:
            # 1. Backup original resolv.conf (only once)
            if RESOLV_CONF.exists() and not RESOLV_ORIGINAL.exists():
                shutil.copy2(RESOLV_CONF, RESOLV_ORIGINAL)
                logger.info(f"Original DNS backed up to {RESOLV_ORIGINAL}")

            # 2. Write new resolv.conf
            new_content = self._config.to_resolv_conf()
            if self.dry_run:
                logger.info(f"[DRY RUN] Would write to {RESOLV_CONF}:")
                logger.info(new_content)
            else:
                RESOLV_CONF.write_text(new_content)
                # Lock the file (immutable) so NetworkManager can't overwrite
                self._set_immutable(RESOLV_CONF, True)

            self._active = True
            logger.info(f"✅ DNS filter enabled: {self._config.name}")
            logger.info(f"   Primary  : {self._config.primary}")
            logger.info(f"   Secondary: {self._config.secondary}")
            logger.info(f"   Blocks   : {', '.join(self._config.blocks)}")
            return True

        except PermissionError:
            logger.error("Permission denied writing resolv.conf — need sudo")
            return False
        except Exception as e:
            logger.error(f"Failed to enable DNS filter: {e}")
            return False

    def disable(self) -> bool:
        """
        Matikan DNS filtering, kembalikan DNS asli.
        """
        if not self._check_root():
            logger.error("DNS filter requires root privileges.")
            return False

        try:
            # Unlock the file first
            if not self.dry_run:
                self._set_immutable(RESOLV_CONF, False)

            # Restore original
            if RESOLV_ORIGINAL.exists():
                if self.dry_run:
                    logger.info(f"[DRY RUN] Would restore {RESOLV_ORIGINAL} → {RESOLV_CONF}")
                else:
                    shutil.copy2(RESOLV_ORIGINAL, RESOLV_CONF)
                    RESOLV_ORIGINAL.unlink()
                    logger.info("✅ Original DNS restored")
            else:
                # Fallback: use Google DNS
                fallback = "nameserver 8.8.8.8\nnameserver 8.8.4.4\n"
                if not self.dry_run:
                    RESOLV_CONF.write_text(fallback)
                logger.warning("Original DNS not found — restored to Google DNS fallback")

            self._active = False
            return True

        except Exception as e:
            logger.error(f"Failed to disable DNS filter: {e}")
            return False

    def test_filtering(self, test_domain: str = "adult-test.com") -> bool:
        """
        Test apakah DNS filtering aktif dengan mencoba resolve blocked domain.
        Returns True jika domain berhasil diblokir (resolve ke 0.0.0.0 atau gagal).
        """
        try:
            import socket
            addr = socket.gethostbyname(test_domain)
            # If it resolves to a blocking address (NXDOMAIN / 0.0.0.0)
            blocked = addr in ("0.0.0.0", "::1", "127.0.0.1")
            logger.info(f"Test domain '{test_domain}' → {addr} ({'BLOCKED ✅' if blocked else 'NOT BLOCKED ⚠️'})")
            return blocked
        except OSError:
            # DNS resolution failed = domain is blocked
            logger.info(f"Test domain '{test_domain}' → NXDOMAIN (BLOCKED ✅)")
            return True

    def get_current_dns(self) -> List[str]:
        """Get current DNS servers from resolv.conf."""
        dns_servers = []
        try:
            if RESOLV_CONF.exists():
                for line in RESOLV_CONF.read_text().splitlines():
                    line = line.strip()
                    if line.startswith("nameserver"):
                        parts = line.split()
                        if len(parts) >= 2:
                            dns_servers.append(parts[1])
        except Exception as e:
            logger.error(f"Error reading resolv.conf: {e}")
        return dns_servers

    def status(self) -> dict:
        """Return current status as dict."""
        current = self.get_current_dns()
        is_our_dns = (
            self._config.primary in current or
            self._config.secondary in current
        )
        return {
            "active":           is_our_dns,
            "provider":         self._config.name,
            "primary":          self._config.primary,
            "secondary":        self._config.secondary,
            "current_dns":      current,
            "blocks":           self._config.blocks,
        }

    @staticmethod
    def _check_root() -> bool:
        """Check if running as root."""
        return os.geteuid() == 0 if hasattr(os, 'geteuid') else False

    @staticmethod
    def _set_immutable(path: Path, immutable: bool):
        """Set/unset file immutable flag using chattr (Linux)."""
        flag = "+i" if immutable else "-i"
        try:
            subprocess.run(["chattr", flag, str(path)],
                           check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # chattr not available or failed — not critical
            pass

    def __repr__(self):
        return (f"DNSFilter(provider={self.provider.value}, "
                f"active={self._active})")


# ────────────────────────────────────────────────────
#  Quick test / demo
# ────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("SafeKid Flash — DNS Filter")
    print("-" * 40)

    # Show available providers
    print("\nAvailable DNS Providers:")
    for provider, config in DNS_PROVIDERS.items():
        print(f"  [{provider.value:26}] {config.name}")
        print(f"    Primary: {config.primary}, Secondary: {config.secondary}")
        print(f"    Blocks: {', '.join(config.blocks)}")
        print()

    # Demo (dry run — safe on any OS)
    f = DNSFilter(provider=DNSProvider.OPENDNS_FAMILY, dry_run=True)
    print(f"\nDry run test: {f}")
    print(f"\nresolv.conf content that would be written:")
    print("-" * 40)
    print(f.config.to_resolv_conf())
    print("-" * 40)
    print("\nStatus:")
    import json
    print(json.dumps(f.status(), indent=2))
