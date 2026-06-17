#!/usr/bin/env python3
"""Tự sinh index PROJECT_MAP cho firmware (drift-proof).

Quét components/ của firmware ESP-IDF, trích:
  - Hàm public trong include/*.h  (component, symbol, file:line)
  - Hằng số #define dạng UPPER_CASE
  - Thành viên enum (FSM states / event ids...) trong *.h
  - Các MQTT topic chuỗi "eldercare/..." trong *.c

Xuất ra: project_setup/architecture/PROJECT_MAP.generated.md
File auto-gen này KHÁC PROJECT_MAP.md (bản tay) — dùng để đối chiếu/rà drift.

Dùng:
    python tools/gen_project_map.py [đường_dẫn_firmware]
Mặc định firmware = ../../firmware/HAR-and-Fall-detection-firmware so với script.
"""
import os
import re
import sys
import glob
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.dirname(SCRIPT_DIR)                 # datn-agent-skills/
REPO_ROOT = os.path.dirname(SKILLS_DIR)                  # datn/
OUT_PATH = os.path.join(SKILLS_DIR, "project_setup", "architecture", "PROJECT_MAP.generated.md")


def find_fw_root():
    """Tự dò gốc project firmware (chứa thư mục components/), portable cả 2 layout:
       máy gốc 'firmware/' chứa code trực tiếp, hoặc clone về 'firmware/<tên-repo>/'."""
    base = os.path.join(REPO_ROOT, "firmware")
    candidates = [base]
    if os.path.isdir(base):
        candidates += [os.path.join(base, d) for d in sorted(os.listdir(base))
                       if os.path.isdir(os.path.join(base, d))]
    for c in candidates:
        if os.path.isdir(os.path.join(c, "components")):
            return os.path.abspath(c)
    return os.path.abspath(base)


# Cho phép truyền tay; mặc định tự dò.
FW = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else find_fw_root()

# Từ khoá không phải tên hàm (loại nhầm)
RESERVED = {"if", "for", "while", "switch", "return", "sizeof", "typedef"}
# Regex prototype 1 dòng:  <kiểu trả về...> <tên>(<args>);
PROTO_RE = re.compile(r"^[A-Za-z_][\w\s\*]+?\b([A-Za-z_]\w*)\s*\([^;{]*\)\s*;\s*$")
DEFINE_RE = re.compile(r"^\s*#define\s+([A-Z][A-Z0-9_]{2,})\s+(\S.*?)\s*$")
ENUM_OPEN_RE = re.compile(r"typedef\s+enum")
ENUM_MEMBER_RE = re.compile(r"^\s*([A-Z][A-Z0-9_]+)\b")
TOPIC_RE = re.compile(r'"(eldercare/[^"]*)"')


def rel(path):
    """Tương đối với GỐC FIRMWARE (vd 'components/svc_imu/...') → portable, không
    phụ thuộc có hay không thư mục con trùng tên repo trên từng máy."""
    return os.path.relpath(path, FW).replace("\\", "/")


def scan_headers():
    """Trả về dict {component: [(symbol, file:line)]}."""
    out = {}
    for hdr in glob.glob(os.path.join(FW, "components", "*", "include", "*.h")):
        comp = hdr.replace("\\", "/").split("/components/")[1].split("/")[0]
        try:
            lines = open(hdr, encoding="utf-8", errors="ignore").read().splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            s = line.strip()
            if not s or s[0] in "#/*}" or s.startswith("//"):
                continue
            m = PROTO_RE.match(s)
            if not m:
                continue
            name = m.group(1)
            if name in RESERVED or "(*" in s:  # bỏ function-pointer typedef
                continue
            out.setdefault(comp, []).append((name, f"{rel(hdr)}:{i}"))
    return out


def scan_defines():
    out = []
    for hdr in glob.glob(os.path.join(FW, "components", "*", "include", "*.h")):
        try:
            lines = open(hdr, encoding="utf-8", errors="ignore").read().splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            m = DEFINE_RE.match(line)
            if m:
                val = m.group(2).split("//")[0].split("/*")[0].strip()
                out.append((m.group(1), val, f"{rel(hdr)}:{i}"))
    return out


def scan_enums():
    """Trích thành viên enum trong *.h (states, event ids...)."""
    out = []
    for hdr in glob.glob(os.path.join(FW, "components", "*", "include", "*.h")):
        try:
            text = open(hdr, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        # Mỗi block 'typedef enum { ... } name;'
        for blk in re.findall(r"typedef\s+enum\s*\{(.*?)\}\s*(\w+)\s*;", text, re.S):
            body, ename = blk
            members = []
            for ln in body.splitlines():
                mm = ENUM_MEMBER_RE.match(ln)
                if mm:
                    members.append(mm.group(1))
            if members:
                out.append((ename, members, rel(hdr)))
    return out


def scan_topics():
    found = {}
    for src in glob.glob(os.path.join(FW, "components", "*", "*.c")):
        try:
            lines = open(src, encoding="utf-8", errors="ignore").read().splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            for t in TOPIC_RE.findall(line):
                found.setdefault(t, f"{rel(src)}:{i}")
    return found


def main():
    if not os.path.isdir(FW):
        sys.exit(f"[!] Không thấy firmware tại: {FW}\n    Truyền đường dẫn: python gen_project_map.py <fw_path>")

    headers = scan_headers()
    defines = scan_defines()
    enums = scan_enums()
    topics = scan_topics()

    L = []
    L.append("# PROJECT MAP (AUTO-GENERATED)")
    L.append("")
    L.append(f"> Sinh tự động bởi `tools/gen_project_map.py` lúc {datetime.now():%Y-%m-%d %H:%M}.")
    L.append("> KHÔNG sửa tay file này — sửa code rồi chạy lại script. Bản tay (có diễn giải): `PROJECT_MAP.md`.")
    L.append(">")
    L.append("> Mọi `path:line` TƯƠNG ĐỐI VỚI GỐC PROJECT FIRMWARE (vd `components/svc_imu/...`),")
    L.append("> portable bất kể firmware nằm ở `firmware/` (máy gốc) hay `firmware/<repo>/` (máy clone).")
    L.append("")

    L.append("## Public API theo component")
    for comp in sorted(headers):
        syms = ", ".join(f"`{n}` ({loc})" for n, loc in headers[comp])
        L.append(f"- **{comp}**: {syms}")
    L.append("")

    L.append("## Enum (FSM states / event ids / class...)")
    for ename, members, loc in sorted(enums):
        L.append(f"- `{ename}` ({loc}): {', '.join(members)}")
    L.append("")

    L.append("## Hằng số (#define)")
    for name, val, loc in sorted(defines):
        L.append(f"- `{name} = {val}` ({loc})")
    L.append("")

    L.append("## MQTT topics (chuỗi trong code)")
    for t in sorted(topics):
        L.append(f"- `{t}` ({topics[t]})")
    L.append("")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print(f"[ok] Wrote {os.path.relpath(OUT_PATH, SKILLS_DIR)} (fw root: {os.path.relpath(FW, REPO_ROOT)})")
    print(f"     {sum(len(v) for v in headers.values())} funcs, {len(defines)} defines, "
          f"{len(enums)} enums, {len(topics)} topics.")


if __name__ == "__main__":
    main()
