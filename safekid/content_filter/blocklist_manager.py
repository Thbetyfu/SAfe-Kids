"""
SafeKid Flash — Blocklist Manager
====================================
Mengunduh dan mengelola daftar domain yang diblokir dari sumber terpercaya.

Sumber blocklist yang didukung:
  • StevenBlack/hosts   — Adult, gambling, violence
  • oisd.nl             — Comprehensive ad/malware/adult
  • hagezi/dns-blocklists — Multi-level blocking
  • urlhaus             — Malware URL blocklist

Format:
  Setiap blocklist adalah file text berisi domain per baris
  atau format hosts (0.0.0.0 domain.com)

Storage:
  /etc/safekid/blocklists/   (Linux)
  %APPDATA%/SafeKidFlash/blocklists/  (Windows — untuk testing)
"""

import hashlib
import json
import logging
import os
import platform
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger("safekid.blocklist")

# ── Storage paths ─────────────────────────────────
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    _BASE_DIR = Path(os.environ.get("APPDATA", ".")) / "SafeKidFlash"
else:
    _BASE_DIR = Path("/etc/safekid")

BLOCKLIST_DIR  = _BASE_DIR / "blocklists"
METADATA_FILE  = _BASE_DIR / "blocklist_meta.json"
COMBINED_FILE  = _BASE_DIR / "combined_blocklist.txt"

# ── HTTP Settings ─────────────────────────────────
USER_AGENT  = "SafeKidFlash/1.0 (Blocklist Updater)"
TIMEOUT_SEC = 30


# ────────────────────────────────────────────────────
#  Blocklist Source Definitions
# ────────────────────────────────────────────────────

class BlockCategory(Enum):
    ADULT      = "adult"
    GAMBLING   = "gambling"
    VIOLENCE   = "violence"
    MALWARE    = "malware"
    PHISHING   = "phishing"
    ADS        = "ads"
    SOCIAL     = "social_media"
    GAMES      = "online_games"


@dataclass
class BlocklistSource:
    id:          str
    name:        str
    url:         str
    categories:  List[BlockCategory]
    size_estimate: str    = "?"     # approximate size hint
    format:      str      = "hosts" # "hosts" or "domains"
    enabled:     bool     = True
    description: str      = ""

    @property
    def local_path(self) -> Path:
        return BLOCKLIST_DIR / f"{self.id}.txt"


# ── Pre-defined sources ───────────────────────────────
BUILTIN_SOURCES = [
    BlocklistSource(
        id="stevenblack_adult",
        name="StevenBlack Adult",
        url="https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/fakenews-gambling-porn/hosts",
        categories=[BlockCategory.ADULT, BlockCategory.GAMBLING],
        size_estimate="~100k domains",
        format="hosts",
        description="StevenBlack hosts — Adult + Gambling + Fake News",
    ),
    BlocklistSource(
        id="oisd_small",
        name="OISD Small",
        url="https://small.oisd.nl/",
        categories=[BlockCategory.ADS, BlockCategory.MALWARE, BlockCategory.PHISHING],
        size_estimate="~75k domains",
        format="domains",
        description="OISD small — Balanced ad/malware blocking",
    ),
    BlocklistSource(
        id="urlhaus_malware",
        name="URLHaus Malware",
        url="https://urlhaus.abuse.ch/downloads/hostfile/",
        categories=[BlockCategory.MALWARE],
        size_estimate="~50k URLs",
        format="hosts",
        description="Abuse.ch URLHaus — Active malware sites",
    ),
    BlocklistSource(
        id="hagezi_gambling",
        name="Hagezi Gambling",
        url="https://raw.githubusercontent.com/hagezi/dns-blocklists/main/hosts/gambling.txt",
        categories=[BlockCategory.GAMBLING],
        size_estimate="~5k domains",
        format="hosts",
        description="Hagezi gambling blocklist",
    ),
    BlocklistSource(
        id="hagezi_adult",
        name="Hagezi Adult",
        url="https://raw.githubusercontent.com/hagezi/dns-blocklists/main/hosts/porn.txt",
        categories=[BlockCategory.ADULT],
        size_estimate="~150k domains",
        format="hosts",
        description="Hagezi adult content blocklist",
    ),
    BlocklistSource(
        id="safekid_custom",
        name="SafeKid Custom",
        url="",    # local only
        categories=[BlockCategory.ADULT, BlockCategory.VIOLENCE],
        size_estimate="custom",
        format="domains",
        description="Local custom blocklist — edit manually",
        enabled=True,
    ),
]


# ────────────────────────────────────────────────────
#  Blocklist Manager
# ────────────────────────────────────────────────────

class BlocklistManager:
    """
    Mengelola daftar domain yang diblokir untuk SafeKid Flash.

    Contoh penggunaan:
        mgr = BlocklistManager()
        mgr.update_all()                       # download semua
        mgr.build_combined()                   # gabungkan jadi 1 file
        print(f"Total: {mgr.total_blocked:,} domains")
        print(mgr.is_blocked("pornhub.com"))   # True
    """

    def __init__(self, sources: Optional[List[BlocklistSource]] = None):
        self.sources      = sources or BUILTIN_SOURCES
        self._domains_set: Optional[Set[str]] = None
        self._meta: Dict[str, dict] = {}
        self._ensure_dirs()
        self._load_meta()

    # ── Setup ─────────────────────────────────────

    def _ensure_dirs(self):
        BLOCKLIST_DIR.mkdir(parents=True, exist_ok=True)
        # Create empty custom blocklist if not exists
        custom = BLOCKLIST_DIR / "safekid_custom.txt"
        if not custom.exists():
            custom.write_text(
                "# SafeKid Flash — Custom Blocklist\n"
                "# Tambahkan domain yang ingin diblokir, satu per baris:\n"
                "# Contoh:\n"
                "# instagram.com\n"
                "# tiktok.com\n",
                encoding="utf-8"
            )

    def _load_meta(self):
        if METADATA_FILE.exists():
            try:
                self._meta = json.loads(METADATA_FILE.read_text())
            except Exception:
                self._meta = {}

    def _save_meta(self):
        try:
            METADATA_FILE.write_text(json.dumps(self._meta, indent=2))
        except Exception as e:
            logger.warning(f"Could not save metadata: {e}")

    # ── Download ──────────────────────────────────

    def update_source(self, source: BlocklistSource,
                       force: bool = False) -> bool:
        """
        Download ulang satu blocklist source.
        Returns True jika berhasil.
        """
        if not source.url:
            logger.info(f"Skipping {source.id} (local only)")
            return True

        # Check if update needed (max once per day)
        meta    = self._meta.get(source.id, {})
        last_ok = meta.get("last_updated", 0)
        if not force and time.time() - last_ok < 86400:
            logger.info(f"[{source.id}] Up to date (updated < 24h ago)")
            return True

        logger.info(f"Downloading {source.name}...")
        try:
            req  = Request(source.url, headers={"User-Agent": USER_AGENT})
            resp = urlopen(req, timeout=TIMEOUT_SEC)
            raw  = resp.read().decode("utf-8", errors="replace")

            count = self._save_blocklist(source, raw)

            self._meta[source.id] = {
                "last_updated": time.time(),
                "domain_count": count,
                "size_bytes":   len(raw),
                "name":         source.name,
            }
            self._save_meta()
            self._domains_set = None   # Invalidate cache
            logger.info(f"✅ {source.name}: {count:,} domains saved")
            return True

        except URLError as e:
            logger.error(f"❌ Download failed for {source.id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error downloading {source.id}: {e}")
            return False

    def update_all(self, force: bool = False,
                   categories: Optional[List[BlockCategory]] = None) -> Dict[str, bool]:
        """
        Download semua blocklists yang diaktifkan.
        Optionally filter by category.
        Returns dict of {source_id: success}.
        """
        results = {}
        for source in self.sources:
            if not source.enabled:
                continue
            if categories and not any(c in categories for c in source.categories):
                continue
            results[source.id] = self.update_source(source, force)
        return results

    def _save_blocklist(self, source: BlocklistSource, raw: str) -> int:
        """Parse and save blocklist file. Returns domain count."""
        domains = self._parse_blocklist(raw, source.format)
        content = "\n".join(sorted(domains)) + "\n"
        source.local_path.write_text(content, encoding="utf-8")
        return len(domains)

    @staticmethod
    def _parse_blocklist(raw: str, fmt: str) -> Set[str]:
        """Parse hosts or plain domains format into set of domains."""
        domains: Set[str] = set()
        domain_re = re.compile(
            r'^(?!-)[A-Za-z0-9\-]{1,63}(?<!-)(\.[A-Za-z0-9\-]{1,63}(?<!-))*\.[A-Za-z]{2,}$'
        )

        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith(("#", "!", "//", ";")):
                continue
            if fmt == "hosts":
                # Format: "0.0.0.0 domain.com" or "127.0.0.1 domain.com"
                parts = line.split()
                if len(parts) >= 2 and parts[0] in ("0.0.0.0", "127.0.0.1", "::1"):
                    domain = parts[1].lower().lstrip("*.")
                    if domain and domain_re.match(domain):
                        domains.add(domain)
            else:
                # Plain domain format
                domain = line.lower().lstrip("*.")
                if domain and domain_re.match(domain):
                    domains.add(domain)

        return domains

    # ── Combined Blocklist ────────────────────────

    def build_combined(self) -> int:
        """
        Gabungkan semua blocklist yang ada menjadi satu file.
        Returns total domain count.
        """
        all_domains: Set[str] = set()

        for source in self.sources:
            if not source.enabled:
                continue
            if source.local_path.exists():
                domains = set(
                    line.strip() for line in source.local_path.read_text().splitlines()
                    if line.strip() and not line.startswith("#")
                )
                all_domains |= domains
                logger.debug(f"{source.id}: {len(domains):,} domains")

        total = len(all_domains)
        content = (
            f"# SafeKid Flash Combined Blocklist\n"
            f"# Generated: {datetime.now().isoformat()}\n"
            f"# Total: {total:,} domains\n\n"
        ) + "\n".join(sorted(all_domains)) + "\n"

        COMBINED_FILE.write_text(content, encoding="utf-8")
        self._domains_set = all_domains
        logger.info(f"✅ Combined blocklist: {total:,} domains → {COMBINED_FILE}")
        return total

    # ── Lookup ────────────────────────────────────

    def _load_combined(self):
        """Load combined blocklist into memory set."""
        if COMBINED_FILE.exists():
            self._domains_set = set(
                line.strip() for line in COMBINED_FILE.read_text().splitlines()
                if line.strip() and not line.startswith("#")
            )
        else:
            # No combined file yet — load from individual source files
            self._domains_set = set()
            for source in self.sources:
                if source.enabled and source.local_path.exists():
                    for line in source.local_path.read_text(encoding="utf-8").splitlines():
                        line = line.strip().split()[0] if line.strip() else ""
                        if line and not line.startswith("#"):
                            self._domains_set.add(line.lower())

    def is_blocked(self, domain: str) -> bool:
        """Check if a domain (or its parent) is in the blocklist."""
        if self._domains_set is None:
            self._load_combined()

        domain = domain.lower().rstrip(".")
        if domain in self._domains_set:
            return True

        # Check parent domains (e.g., sub.adult.com → adult.com)
        parts = domain.split(".")
        for i in range(1, len(parts) - 1):
            parent = ".".join(parts[i:])
            if parent in self._domains_set:
                return True
        return False

    def add_domain(self, domain: str, category: str = "custom") -> bool:
        """Add a domain to the custom blocklist and in-memory set."""
        custom_path = BLOCKLIST_DIR / "safekid_custom.txt"
        domain = domain.lower().strip()
        try:
            existing = custom_path.read_text(encoding="utf-8")
            if domain in existing:
                logger.info(f"Domain {domain} already in custom list")
                # Still add to in-memory set if loaded
                if self._domains_set is not None:
                    self._domains_set.add(domain)
                return True
            with open(custom_path, "a", encoding="utf-8") as f:
                f.write(f"{domain}  # {category}\n")
            # Update in-memory set immediately (no need to reload file)
            if self._domains_set is None:
                self._load_combined()
            if self._domains_set is not None:
                self._domains_set.add(domain)
            logger.info(f"Added {domain} to custom blocklist")
            return True
        except Exception as e:
            logger.error(f"Failed to add domain: {e}")
            return False

    def remove_domain(self, domain: str) -> bool:
        """Remove a domain from the custom blocklist."""
        custom_path = BLOCKLIST_DIR / "safekid_custom.txt"
        domain = domain.lower().strip()
        try:
            lines = custom_path.read_text(encoding="utf-8").splitlines()
            new_lines = [l for l in lines if not l.startswith(domain)]
            custom_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            self._domains_set = None
            return True
        except Exception as e:
            logger.error(f"Failed to remove domain: {e}")
            return False

    # ── Stats ─────────────────────────────────────

    @property
    def total_blocked(self) -> int:
        if self._domains_set is None:
            self._load_combined()
        return len(self._domains_set)

    def get_stats(self) -> dict:
        return {
            "total_blocked":   self.total_blocked,
            "sources_enabled": sum(1 for s in self.sources if s.enabled),
            "combined_file":   str(COMBINED_FILE),
            "blocklist_dir":   str(BLOCKLIST_DIR),
            "sources": {
                s.id: {
                    "name":    s.name,
                    "enabled": s.enabled,
                    "downloaded": s.local_path.exists(),
                    "count":   self._meta.get(s.id, {}).get("domain_count", 0),
                    "updated": datetime.fromtimestamp(
                        self._meta.get(s.id, {}).get("last_updated", 0)
                    ).strftime("%Y-%m-%d %H:%M") if s.id in self._meta else "never",
                }
                for s in self.sources
            },
        }

    def __repr__(self):
        return f"BlocklistManager({len(self.sources)} sources, {self.total_blocked:,} blocked)"


# ────────────────────────────────────────────────────
#  Quick Test
# ────────────────────────────────────────────────────
if __name__ == "__main__":
    import json as _json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("SafeKid Flash — Blocklist Manager")
    print("-" * 50)

    mgr = BlocklistManager()
    print(f"\nStorage dir  : {BLOCKLIST_DIR}")
    print(f"Combined file: {COMBINED_FILE}")
    print(f"Total sources: {len(mgr.sources)}")

    print("\nSources:")
    for s in mgr.sources:
        print(f"  {'✅' if s.enabled else '❌'} [{s.id:25}] {s.name}")
        print(f"     Categories: {[c.value for c in s.categories]}")
        print(f"     Size: {s.size_estimate}")
        print()

    print("\nStats:")
    print(_json.dumps(mgr.get_stats(), indent=2))

    # Demo: add custom domain
    print("\nAdding test domain to custom list...")
    mgr.add_domain("example-test-block.com", "test")

    print("\n✅ Blocklist Manager ready!")
    print("Run: mgr.update_all() to download blocklists (requires internet)")
