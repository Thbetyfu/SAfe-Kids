# 🤝 Contributing to SafeKid Flash

Terima kasih sudah tertarik berkontribusi di SafeKid Flash! Dokumen ini menjelaskan cara kontribusi yang baik.

---

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Development Setup](#development-setup)
3. [How to Contribute](#how-to-contribute)
4. [Code Style](#code-style)
5. [Testing](#testing)
6. [Commit Messages](#commit-messages)
7. [Pull Request Process](#pull-request-process)

---

## ✅ Code of Conduct

Proyek ini mengikuti prinsip **ramah & inklusif**:
- Hormati semua kontributor
- Fokus pada membantu anak-anak Indonesia lebih aman di internet
- Gunakan bahasa yang sopan di issues dan PR

---

## 🛠️ Development Setup

```bash
# 1. Fork & clone repo
git clone https://github.com/Thbetyfu/SAfe-Kids.git
cd SAfe-Kids

# 2. Install Python 3.9+
# Download: https://python.org/downloads

# 3. Install dependencies
pip install -r requirements.txt        # Production
pip install -r requirements-dev.txt   # Development (pytest, flake8, dll)

# 4. Jalankan server demo
python safekid/kid_ui/launcher_server.py --demo

# 5. Buka UI
# http://localhost:5556/
```

---

## 🎯 How to Contribute

### Jenis Kontribusi yang Diterima:

| Jenis | Contoh |
|-------|--------|
| 🐛 Bug Fix | Perbaiki error di `launcher_server.py` |
| ✨ Feature | Tambah tema baru (winter, sunset) |
| 📱 App | Tambah app edukasi baru di `apps_catalog.json` |
| 🌐 Terjemahan | Tambah bahasa baru di `safekid/i18n.py` |
| 📖 Dokumentasi | Perbaiki README, CHANGELOG, BUILD_GUIDE |
| 🧪 Tests | Tambah test case di `tests/` |

### Langkah Kontribusi:

```bash
# 1. Buat branch baru
git checkout -b feature/nama-fitur
# atau
git checkout -b fix/nama-bug

# 2. Edit kode
# ...

# 3. Jalankan tests
python run_tests.py

# 4. Commit
git commit -m "feat: deskripsi singkat fitur"

# 5. Push & buat PR
git push origin feature/nama-fitur
```

---

## 🎨 Menambah App Edukasi Baru

Edit `safekid/apps/apps_catalog.json`:

```json
{
  "id": "app-unik-id",
  "name": "Nama Aplikasi",
  "icon": "🎮",
  "description": "Deskripsi singkat app (maks 80 karakter)",
  "category": "edu",
  "color": "#4ECDC4",
  "badge": "Edu",
  "min_age": 5,
  "max_age": 12,
  "linux_cmd": "nama-perintah-di-linux",
  "windows_url": "https://website-download.com",
  "website": "https://website-resmi.com",
  "enabled": true
}
```

**Kategori yang tersedia:** `edu`, `game`, `creative`, `web`

**Kriteria app yang diterima:**
- ✅ Open-source atau gratis
- ✅ Aman untuk anak-anak
- ✅ Tersedia di Linux (dan/atau Windows)
- ❌ Tidak ada konten berbayar tersembunyi (in-app purchase agresif)

---

## 🌐 Menambah Bahasa Baru

Edit `safekid/i18n.py` — tambahkan kode bahasa baru di `TRANSLATIONS`:

```python
TRANSLATIONS = {
    "id": { ... },
    "en": { ... },
    # Tambahkan di sini:
    "jv": {  # Bahasa Jawa
        "welcome": "Sugeng rawuh, {name}!",
        "time_left": "Wektu Sisa",
        # ...
    }
}
SUPPORTED_LANGS = ["id", "en", "jv"]  # Update ini juga
```

Pastikan semua 38 kunci tersedia di bahasa baru. Jalankan:
```bash
python -m pytest tests/test_i18n_updater.py
```

---

## 🧪 Testing

```bash
# Jalankan semua test
python run_tests.py

# Jalankan dengan coverage
python -m pytest tests/ --cov=safekid --cov-report=term-missing

# Jalankan test tertentu
python -m pytest tests/test_server.py -v
```

**Aturan:**
- Semua PR harus: **28/28 tests PASS** (atau lebih)
- Jangan hapus test yang sudah ada
- Untuk fitur baru: wajib tambah minimal 1 test

---

## 📝 Code Style

```bash
# Format kode dengan Black
black safekid/ tests/ --line-length 120

# Cek linting
flake8 safekid/ --max-line-length=120

# Type checking
mypy safekid/i18n.py safekid/updater.py
```

**Aturan:**
- Max line length: **120 karakter**
- Gunakan **type hints** untuk fungsi baru
- Tulis **docstring** untuk class dan fungsi publik
- Gunakan **Bahasa Indonesia** untuk comment dan docstring dalam kode (konsistens dengan proyek)

---

## 💬 Commit Messages

Format: `type: deskripsi singkat`

| Type | Kapan digunakan |
|------|----------------|
| `feat` | Fitur baru |
| `fix` | Perbaikan bug |
| `docs` | Perubahan dokumentasi |
| `test` | Tambah/perbaiki test |
| `refactor` | Refactor tanpa tambah fitur |
| `style` | Perubahan format/style |
| `chore` | Update dependencies, CI |

```
feat: Tambah tema winter untuk launcher UI
fix: Perbaiki crash saat catalog.json kosong
docs: Update BUILD_GUIDE untuk Ubuntu 24.04
test: Tambah test coverage untuk theme switcher
```

---

## 🔄 Pull Request Process

1. **Update CHANGELOG.md** — tambahkan entry di `[Unreleased]`
2. **Pastikan semua tests pass** — `python run_tests.py`
3. **Isi PR Template** (lihat section di bawah)
4. **Minta review** dari maintainer
5. **Squash commits** jika diminta

### PR Template:
```markdown
## Deskripsi
Apa yang berubah dan mengapa?

## Jenis Perubahan
- [ ] Bug fix
- [ ] Fitur baru
- [ ] Dokumentasi

## Testing
- [ ] Semua test pass (`python run_tests.py`)
- [ ] Test baru ditambahkan (jika ada fitur baru)

## Screenshot (jika ada perubahan UI)
```

---

## 📮 Kontak

- **Issues**: [GitHub Issues](https://github.com/Thbetyfu/SAfe-Kids/issues)
- **Diskusi**: [GitHub Discussions](https://github.com/Thbetyfu/SAfe-Kids/discussions)

---

*Dibuat untuk keamanan digital anak-anak Indonesia* 🇮🇩
