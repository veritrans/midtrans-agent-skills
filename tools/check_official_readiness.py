#!/usr/bin/env python3
"""Local official-readiness checks for the Midtrans Agent Skills repo."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "integrate-midtrans-payments"
SKILL_MD = SKILL / "SKILL.md"
INDEX = ROOT / ".well-known" / "skills" / "index.json"
EVALUATIONS = SKILL / "evaluations.json"
LICENSE = ROOT / "LICENSE"
DOC_LINK_RE = re.compile(r"https://docs\.midtrans\.com/[^\s)\]\[(`\"<]+")


def ok(message: str) -> None:
    print(f"ok: {message}")


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def run(cmd: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=merged_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def require_success(cmd: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    result = run(cmd, cwd=cwd, env=env)
    if result.returncode != 0:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        fail(f"command failed ({result.returncode}): {' '.join(cmd)}")


def load_json(path: Path) -> object:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # noqa: BLE001 - report any parse/read failure uniformly.
        fail(f"{path.relative_to(ROOT)} is not valid JSON: {exc}")


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        fail("SKILL.md must start with YAML frontmatter")
    data: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        if not raw_line.strip():
            continue
        if ":" not in raw_line:
            fail(f"cannot parse frontmatter line: {raw_line}")
        key, value = raw_line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        data[key.strip()] = value
    return data


def check_skill_metadata() -> None:
    text = SKILL_MD.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    allowed = {"name", "description", "license", "allowed-tools", "metadata"}
    unexpected = sorted(set(frontmatter) - allowed)
    if unexpected:
        fail(f"unexpected SKILL.md frontmatter keys: {', '.join(unexpected)}")
    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        fail(f"invalid skill name: {name!r}")
    if not description:
        fail("SKILL.md description is required")
    if "<" in description or ">" in description:
        fail("SKILL.md description cannot contain angle brackets")
    if len(description) > 1024:
        fail("SKILL.md description exceeds 1024 characters")
    if SKILL_MD.stat().st_size >= 16 * 1024:
        fail("SKILL.md must stay under 16 KiB per PRD")
    ok("skill metadata and size")


def check_versions_and_manifest() -> None:
    index = load_json(INDEX)
    evaluations = load_json(EVALUATIONS)
    if not isinstance(index, dict) or not isinstance(evaluations, dict):
        fail("index and evaluations must be JSON objects")
    skills = index.get("skills")
    if not isinstance(skills, list) or len(skills) != 1:
        fail("index must contain exactly one skill entry")
    skill_entry = skills[0]
    versions = {index.get("version"), skill_entry.get("version"), evaluations.get("version")}
    if len(versions) != 1:
        fail(f"version mismatch across index/evaluations: {versions}")
    files = skill_entry.get("files")
    if not isinstance(files, list):
        fail("index skill entry must include files list")
    actual = sorted(str(path.relative_to(SKILL)) for path in SKILL.rglob("*") if path.is_file())
    listed = sorted(files)
    missing = [path for path in listed if not (SKILL / path).is_file()]
    extra = [path for path in actual if path not in listed]
    if missing or extra:
        fail(f"manifest mismatch; missing={missing}, extra={extra}")
    ok(f"catalog manifest and version {versions.pop()}")


def check_license() -> None:
    if not LICENSE.is_file():
        fail("LICENSE is required")
    text = LICENSE.read_text(encoding="utf-8")
    required = [
        "BSD 3-Clause License",
        "Copyright (c) 2026, PT Midtrans",
        "Redistribution and use in source and binary forms",
        'THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"',
    ]
    missing = [needle for needle in required if needle not in text]
    if missing:
        fail("LICENSE is missing expected BSD 3-Clause text: " + ", ".join(missing))

    index = load_json(INDEX)
    if not isinstance(index, dict):
        fail("index must be a JSON object")
    if index.get("license") != "BSD-3-Clause":
        fail("index license must be BSD-3-Clause")
    skills = index.get("skills")
    if not isinstance(skills, list) or not skills:
        fail("index must include at least one skill")
    if any(not isinstance(skill, dict) or skill.get("license") != "BSD-3-Clause" for skill in skills):
        fail("each indexed skill must declare BSD-3-Clause")

    frontmatter = parse_frontmatter(SKILL_MD.read_text(encoding="utf-8"))
    if frontmatter.get("license") != "BSD-3-Clause":
        fail("SKILL.md frontmatter license must be BSD-3-Clause")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "[BSD 3-Clause License](LICENSE)" not in readme:
        fail("README must link to the BSD 3-Clause LICENSE")
    ok("BSD 3-Clause license metadata")


def check_json_files() -> None:
    load_json(INDEX)
    load_json(EVALUATIONS)
    for path in (SKILL / "assets" / "fixtures").glob("*.json"):
        load_json(path)
    ok("JSON files and fixtures")


def check_evaluations() -> None:
    result = run([sys.executable, str(ROOT / "tools" / "build_pressure_pack.py"), "--host", "claude-code", "--dry-run"])
    if result.returncode != 0:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        fail("pressure-pack dry run failed")
    ok("pressure scenarios are well-formed")


def check_publication_bundle() -> None:
    result = run([sys.executable, str(ROOT / "tools" / "build_publication_bundle.py"), "--dry-run"])
    if result.returncode != 0:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        fail("publication bundle dry run failed")
    ok("publication bundle is well-formed")


def check_references() -> None:
    missing_llms = []
    for path in (SKILL / "references").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if "https://docs.midtrans.com/llms.txt" not in text:
            missing_llms.append(str(path.relative_to(ROOT)))
    if missing_llms:
        fail("references missing llms.txt pointer: " + ", ".join(missing_llms))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "[LICENSE](LICENSE)" in readme and not (ROOT / "LICENSE").exists():
        fail("README links to LICENSE but LICENSE is not present")
    ok("reference docs point to live Midtrans docs index")


def check_scripts() -> None:
    script_dir = SKILL / "scripts"
    shell_scripts = sorted(script_dir.glob("*.sh"))
    python_scripts = sorted(script_dir.glob("*.py"))
    for path in shell_scripts + python_scripts:
        if not os.access(path, os.X_OK):
            fail(f"script is not executable: {path.relative_to(ROOT)}")
    for path in shell_scripts:
        require_success(["bash", "-n", str(path)])
    require_success([sys.executable, "-m", "py_compile", *map(str, python_scripts), str(Path(__file__).resolve())])
    ok("script syntax, compile, and executable bits")


def check_snap_fixtures() -> None:
    env = {"MIDTRANS_SERVER_KEY": "SB-Mid-server-test"}
    for name in (
        "snap-notification-settlement.json",
        "snap-notification-pending.json",
        "snap-notification-expire.json",
    ):
        require_success(
            [
                str(SKILL / "scripts" / "verify_snap_signature.sh"),
                "--payload",
                str(SKILL / "assets" / "fixtures" / name),
            ],
            env=env,
        )
    ok("deterministic Snap fixture signatures")


def check_safety_behaviors() -> None:
    fixture = str(SKILL / "assets" / "fixtures" / "snap-notification-settlement.json")
    replay = str(SKILL / "scripts" / "replay_snap_webhook.sh")
    remote = run(
        [replay, "--target-url", "https://example.com/hook", "--fixture", fixture],
        env={"MIDTRANS_SERVER_KEY": "SB-Mid-server-test"},
    )
    if remote.returncode != 2 or "Refusing to POST without --remote-target" not in remote.stderr:
        fail("remote Snap replay refusal did not trigger as expected")
    production = run(
        [replay, "--fixture", fixture, "--dry-run"],
        env={"MIDTRANS_SERVER_KEY": "Mid-server-prod"},
    )
    if production.returncode != 2 or "--allow-production" not in production.stderr:
        fail("production-looking server key refusal did not trigger as expected")
    public_key = run(
        [
            str(SKILL / "scripts" / "verify_bisnap_notification.py"),
            "--path",
            "/api/bisnap/notify",
            "--timestamp",
            "2026-05-27T14:30:00+07:00",
            "--signature",
            "abc",
            "--body-file",
            str(SKILL / "assets" / "fixtures" / "bisnap-qris-notification.json"),
        ],
        env={"BISNAP_PUBLIC_KEY": "not-a-key"},
    )
    if public_key.returncode != 2 or "Traceback" in public_key.stderr or "invalid public key input" not in public_key.stderr:
        fail("malformed BI-SNAP public key did not produce the expected clean error")
    ok("credential and target safety behaviors")


def check_doc_links() -> None:
    urls: set[str] = {"https://docs.midtrans.com/llms.txt"}
    for path in [ROOT / "README.md", SKILL_MD, *(SKILL / "references").glob("*.md")]:
        urls.update(DOC_LINK_RE.findall(path.read_text(encoding="utf-8")))

    def check_once(normalized: str) -> str | None:
        try:
            result = subprocess.run(
                [
                    "curl",
                    "--http1.1",
                    "-L",
                    "-sS",
                    "--connect-timeout",
                    "5",
                    "--max-time",
                    "30",
                    "-H",
                    "Upgrade-Insecure-Requests: 1",
                    "-A",
                    "midtrans-agent-skills-readiness-check/1.0",
                    "-o",
                    "/dev/null",
                    "-w",
                    "%{http_code}",
                    normalized,
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=35,
            )
            status_text = result.stdout.strip()
            status = int(status_text) if status_text.isdigit() else 0
            if result.returncode != 0 or status >= 400 or status == 0:
                detail = result.stderr.strip() or f"HTTP {status_text}"
                return f"{normalized}: {detail}"
        except Exception as exc:  # noqa: BLE001 - make external link failures visible.
            return f"{normalized}: {exc}"
        return None

    checked_urls = [
        url.rstrip(".,")
        for url in sorted(urls)
        if "/.well-known/skills/index.json" not in url.rstrip(".,")
    ]
    failures = []
    for normalized in checked_urls:
        failure = check_once(normalized)
        if failure is None:
            continue
        time.sleep(1)
        retry_failure = check_once(normalized)
        if retry_failure is not None:
            failures.append(retry_failure)
    if failures:
        fail("docs link checks failed: " + "; ".join(failures))
    ok(f"Midtrans docs links ({len(checked_urls)} checked)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-doc-links",
        action="store_true",
        help="also fetch docs.midtrans.com links; slower and network-dependent",
    )
    args = parser.parse_args()

    check_skill_metadata()
    check_versions_and_manifest()
    check_license()
    check_json_files()
    check_evaluations()
    check_publication_bundle()
    check_references()
    check_scripts()
    check_snap_fixtures()
    check_safety_behaviors()
    if args.check_doc_links:
        check_doc_links()
    print("official-readiness local checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
