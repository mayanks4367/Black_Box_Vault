# AGENTS.md — Black Box Vault

Agent coding instructions for the Black Box Vault project: a zero-trust secret vault
system comprising a Linux kernel module (C), a Python user-space guard daemon, a
Kivy-based Android mobile app, and a static HTML/JS web page.

---

## Project Structure

```
Black_Box_Vault/
├── vault_driver.c       # Linux kernel character device driver (C)
├── guard.py             # Python TOTP/QR guard daemon (user-space)
├── index.html           # Static QR display web page
├── Makefile             # Kernel module build (kbuild out-of-tree)
├── setup.sh             # Full installation script (Bash)
├── requirements.txt     # Python top-level dependencies
└── vault_app/           # Android mobile app (Python + Kivy)
    ├── main.py          # Kivy application entry point
    ├── test_core.py     # Ad-hoc test script (no pytest discovery)
    └── buildozer.spec   # Android APK build configuration
```

---

## Build Commands

### Kernel Module (C)

```bash
# Build the kernel module
make

# Clean build artifacts
make clean

# Load the module (requires root)
sudo insmod vault_driver.ko

# Unload the module
sudo rmmod vault_driver

# Check module status / kernel logs
lsmod | grep vault_driver
dmesg | tail -30

# Create device node after loading
sudo mknod /dev/secret_vault c $(awk '$2=="vault_driver" {print $1}' /proc/devices) 0
sudo chmod 666 /dev/secret_vault
```

### Python / Guard Daemon

```bash
# Install Python dependencies (top-level)
pip install -r requirements.txt

# Run the guard daemon
python3 guard.py

# Install all system deps + build + load module automatically
sudo bash setup.sh
```

### Android App (Kivy / Buildozer)

```bash
# Build debug APK (first run downloads NDK/SDK — takes time)
cd vault_app
buildozer android debug

# Deploy to connected device
buildozer android deploy run logcat
```

---

## Test Commands

There is no formal test suite yet. The only test file is an ad-hoc script:

```bash
# Run the ad-hoc test script
cd vault_app
python3 test_core.py
```

`pytest` is listed as a dependency and the intended framework. When adding new tests:
- Place them under `tests/` at the repo root or `tests/integration/`
- Use standard pytest conventions (`def test_*` at module level, no manual `main()` runner)
- Run all tests: `python3 -m pytest tests/ -v`
- Run a single test file: `python3 -m pytest tests/test_foo.py -v`
- Run a single test function: `python3 -m pytest tests/test_foo.py::test_function_name -v`

No kernel-space tests (KUnit/kselftest) are present; if added, use:
```bash
sudo ./tools/testing/kunit/kunit.py run
```

---

## Linting & Formatting

No config files are present. Apply these standards manually or via pre-commit hooks.

### C (kernel module)

```bash
# Check against Linux kernel style
perl scripts/checkpatch.pl --no-tree -f vault_driver.c

# Format with clang-format (if available)
clang-format -style="{BasedOnStyle: Linux, IndentWidth: 4}" -i vault_driver.c
```

### Python

```bash
# Style check
flake8 guard.py vault_app/main.py vault_app/test_core.py

# Security audit
bandit -r guard.py vault_app/

# Type checking (encouraged)
mypy guard.py vault_app/main.py
```

---

## Code Style Guidelines

### C — Kernel Module (`vault_driver.c`)

**Indentation & Formatting**
- 4 spaces per indent level (project deviation from Linux-standard tabs)
- Maximum 100 characters per line
- `//` single-line comments are used (project deviation from kernel `/* */` convention)
- Section headers use `// --- SECTION NAME ---` banners

**Naming**
- Functions and variables: `snake_case` (`my_open`, `auto_lock_callback`, `secret_init`)
- Macros and constants: `UPPER_SNAKE_CASE` (`VAULT_MAGIC`, `MAX_SECRET`, `VAULT_PIN`)
- Module init/exit: `module_init()` / `module_exit()` at the bottom of the file

**Error Handling**
- Use the goto-cleanup pattern for multi-resource init failures:
  ```c
  ret = do_thing();
  if (ret < 0)
      goto err_label;
  ```
- Return negative errno values: `-EACCES`, `-EFAULT`, `-EINVAL`, `-ERESTARTSYS`, etc.
- Never return raw positive integers for errors

**Locking**
- Declare mutexes with `DEFINE_MUTEX(name)`
- Always use `mutex_lock_interruptible()` in file ops; fall back to `mutex_lock()` only
  when the context cannot sleep interruptibly
- Every `mutex_lock*` must have a matching `mutex_unlock` on all code paths

**Logging**
- Use `pr_info`, `pr_warn`, `pr_err` (never `printk` directly)
- Prefix all messages with `[Vault]: ` for easy `dmesg` grepping

**Includes**
- All includes are `<linux/...>` kernel headers
- Add a trailing comment explaining non-obvious includes

**Module Metadata** (always at top of file)
```c
MODULE_LICENSE("GPL");
MODULE_AUTHOR("...");
MODULE_DESCRIPTION("...");
MODULE_VERSION("...");
```

---

### Python (`guard.py`, `vault_app/main.py`)

**Indentation & Formatting**
- 4 spaces per indent level (PEP 8)
- Maximum 100 characters per line
- f-strings preferred over `.format()` or `%`

**Imports**
- Order: stdlib → third-party → local; one blank line between groups
- No wildcard imports (`from module import *`)
- No `__future__` imports needed (Python 3.7+ only)

**Naming**
- Functions and variables: `snake_case`
- Classes: `PascalCase` (`VaultKeyApp`, `MainUI`)
- Module-level constants: `UPPER_SNAKE_CASE` (grouped under a `# --- CONFIGURATION ---` block at the top of each file)

**Type Hints**
- Add type hints to all new function signatures (existing code lacks them — fix on touch):
  ```python
  def unlock_vault(pin: int, secret: str) -> bool:
  ```

**Docstrings**
- Module-level triple-quoted docstring required on all files
- Function docstrings use plain one-liner or Google style for complex functions

**Error Handling**
- Never use bare `except:` — always name the exception: `except Exception as e:`
- Never silently swallow exceptions; at minimum log them:
  ```python
  except Exception as e:
      logger.error("Failed to load history: %s", e)
  ```
- Use `finally` for cleanup (file handles, device file descriptors, etc.)
- `KeyboardInterrupt` and `SystemExit` should be caught separately from `Exception`

**Shebang**
- All executable Python scripts must start with `#!/usr/bin/env python3`

**Kivy-specific**
- Embed KV layout strings inline via `Builder.load_string()` (current pattern)
- Store app state as class-level attributes on the `App` subclass

---

### Bash (`setup.sh`)

- Always start with `set -e` and register a `trap` for INT/TERM
- Use named ANSI color constants; print via helper functions (`print_info`, `print_error`, etc.)
- One function per concern; call `main "$@"` as the entry point at the bottom of the file
- Detect package managers at runtime (`command -v apt-get/yum/dnf`); never hardcode one

---

## Security Constraints

This is a security-sensitive codebase. Observe these rules at all times:

- **Never hardcode credentials** — `VAULT_PIN` and `SHARED_SECRET` are placeholders for
  demonstration; real deployments must source them from environment variables or a secrets
  manager. Do not introduce new hardcoded secrets.
- **Never log secret values** — do not `pr_info` or `print()` PIN, TOTP seeds, or derived keys.
- **IOCTL input validation** — all data crossing the user/kernel boundary via `copy_from_user`
  must be fully validated before use.
- **Privilege separation** — the kernel module enforces access control; user-space code must
  not bypass this by writing directly to `/dev/secret_vault` except through the defined IOCTL
  interface.
- Run `bandit -r .` before committing Python changes.

---

## Git & Commit Conventions

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(guard): add TOTP window tolerance configuration
fix(vault_driver): prevent mutex double-unlock on IOCTL error path
docs(readme): update installation prerequisites
chore(gitignore): exclude *.ko and build artifacts
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `security`

Do **not** commit:
- Compiled artifacts (`*.ko`, `*.o`, `*.mod`, `*.mod.c`, `.*.cmd`, `modules.order`, `Module.symvers`)
- Python virtualenvs (`vault_app/venv/`)
- Buildozer caches (`.buildozer/`)

These are all in `.gitignore`; if they are already tracked, remove them with `git rm --cached`.
