# -*- coding: utf-8 -*-
"""
Sinh ERD (Entity-Relationship Diagram) cho CSDL PostgreSQL của hệ thống, bằng matplotlib
(offline, không cần mermaid/chromium). Nguồn schema: Hinhve/erd.mmd (7 bảng, khóa ngoại).
Xuất: report/Do_an_tot_nghiep_Vu_Manh_Hung/Hinhve/erd.png  (dùng cho slide 20 & báo cáo fig:erd).

Chạy: python gen_erd.py   (cần: pip install matplotlib)
Lưu ý: erd.png trước đây bị ghi đè nhầm bằng sơ đồ firmware -> script này khôi phục đúng ERD.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(BASE, "report", "Do_an_tot_nghiep_Vu_Manh_Hung", "Hinhve", "erd.png")

HUST_BLUE = "#003D7A"
HDR_TXT = "#FFFFFF"
PK_C = "#C8102E"   # đỏ cho PK
FK_C = "#1B7A3D"   # xanh lá cho FK
BOX_FILL = "#FFFFFF"
BOX_EDGE = "#003D7A"
REL_C = "#666666"

# (tên bảng, [(field, type, flag)]) flag: 'PK' | 'FK' | ''
TABLES = {
    "organizations": [
        ("id", "UUID", "PK"), ("name", "string", ""), ("address", "string", ""),
        ("created_at", "datetime", ""), ("updated_at", "datetime", ""),
    ],
    "users": [
        ("id", "UUID", "PK"), ("username", "string", ""), ("password_hash", "string", ""),
        ("role", "enum", ""), ("org_id", "UUID", "FK"),
        ("created_at", "datetime", ""), ("updated_at", "datetime", ""),
    ],
    "wearers": [
        ("id", "UUID", "PK"), ("full_name", "string", ""), ("height_cm", "float", ""),
        ("org_id", "UUID", "FK"), ("created_at", "datetime", ""), ("updated_at", "datetime", ""),
    ],
    "devices": [
        ("device_id", "string", "PK"), ("firmware_version", "string", ""),
        ("current_wearer_id", "UUID", "FK"), ("is_active", "bool", ""),
        ("telemetry_interval", "int", ""), ("fall_threshold", "float", ""),
        ("fall_cooldown", "int", ""), ("org_id", "UUID", "FK"), ("battery_pct", "int", ""),
        ("last_rssi", "int", ""), ("last_online", "datetime", ""),
        ("created_at", "datetime", ""), ("updated_at", "datetime", ""),
    ],
    "alerts": [
        ("id", "UUID", "PK"), ("device_id", "string", "FK"), ("wearer_id", "UUID", "FK"),
        ("alert_type", "string", ""), ("confidence", "float", ""), ("is_resolved", "bool", ""),
        ("created_at", "datetime", ""), ("updated_at", "datetime", ""),
    ],
    "device_events": [
        ("id", "UUID", "PK"), ("device_id", "string", "FK"), ("wearer_id", "UUID", "FK"),
        ("event_type", "string", ""), ("description", "string", ""),
        ("created_at", "datetime", ""), ("updated_at", "datetime", ""),
    ],
    "verification_sessions": [
        ("id", "UUID", "PK"), ("device_id", "string", "FK"), ("wearer_id", "UUID", "FK"),
        ("org_id", "UUID", "FK"), ("subject_code", "string", ""), ("activity_code", "string", ""),
        ("trial_no", "string", ""), ("sample_count", "int", ""), ("duration_s", "float", ""),
        ("file_path", "string", ""), ("created_at", "datetime", ""), ("updated_at", "datetime", ""),
    ],
}

# vị trí (x,y) góc trên-trái của mỗi bảng (đơn vị data), bề rộng cố định
BOXW = 4.3
ROWH = 0.40
HDRH = 0.55
POS = {
    "organizations":        (0.3, 12.6),
    "users":                (0.3, 6.2),
    "wearers":              (5.6, 13.2),
    "devices":              (5.6, 7.2),
    "alerts":               (11.2, 13.4),
    "device_events":        (11.2, 8.4),
    "verification_sessions":(11.2, 5.0),
}

# quan hệ: (parent, child, nhãn) — parent(1) --< child(nhiều)
RELS = [
    ("organizations", "users", "has"),
    ("organizations", "wearers", "has"),
    ("organizations", "devices", "owns"),
    ("organizations", "verification_sessions", "owns"),
    ("wearers", "devices", "wears"),
    ("devices", "alerts", "triggers"),
    ("devices", "device_events", "logs"),
    ("devices", "verification_sessions", "records"),
    ("wearers", "alerts", "linked"),
    ("wearers", "device_events", "linked"),
    ("wearers", "verification_sessions", "subject"),
]

boxes = {}  # name -> dict(x,y,w,h, left, right, top, bottom, cx, cy)


def draw_table(ax, name):
    x, ytop = POS[name]
    fields = TABLES[name]
    h = HDRH + ROWH * len(fields)
    y = ytop - h
    # thân bảng
    ax.add_patch(FancyBboxPatch((x, y), BOXW, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                linewidth=1.3, edgecolor=BOX_EDGE, facecolor=BOX_FILL, zorder=3))
    # header
    ax.add_patch(FancyBboxPatch((x, ytop - HDRH), BOXW, HDRH,
                                boxstyle="round,pad=0.02,rounding_size=0.06",
                                linewidth=0, facecolor=HUST_BLUE, zorder=4))
    ax.text(x + BOXW / 2, ytop - HDRH / 2, name, ha="center", va="center",
            fontsize=11, fontweight="bold", color=HDR_TXT, zorder=5, family="monospace")
    # fields
    for i, (fn, ft, flag) in enumerate(fields):
        ry = ytop - HDRH - ROWH * (i + 0.5)
        if i % 2 == 1:
            ax.add_patch(plt.Rectangle((x + 0.02, ry - ROWH / 2), BOXW - 0.04, ROWH,
                                       facecolor="#EEF2F7", edgecolor="none", zorder=3.5))
        tag = ""
        col = "#222222"
        if flag == "PK":
            tag = "  PK"; col = PK_C
        elif flag == "FK":
            tag = "  FK"; col = FK_C
        label = fn + (tag)
        ax.text(x + 0.18, ry, label, ha="left", va="center", fontsize=8.2,
                color=col, fontweight=("bold" if flag else "normal"),
                family="monospace", zorder=5)
        ax.text(x + BOXW - 0.18, ry, ft, ha="right", va="center", fontsize=7.6,
                color="#888888", style="italic", family="monospace", zorder=5)
    boxes[name] = dict(x=x, y=y, w=BOXW, h=h, left=x, right=x + BOXW,
                       top=ytop, bottom=y, cx=x + BOXW / 2, cy=y + h / 2)


def anchor(b, side):
    if side == "L": return (b["left"], b["cy"])
    if side == "R": return (b["right"], b["cy"])
    if side == "T": return (b["cx"], b["top"])
    return (b["cx"], b["bottom"])


def draw_rel(ax, parent, child, label):
    p, c = boxes[parent], boxes[child]
    # chọn cạnh nối theo vị trí tương đối
    if c["cx"] > p["cx"] + 0.5:
        ps, cs = "R", "L"
    elif c["cx"] < p["cx"] - 0.5:
        ps, cs = "L", "R"
    else:  # cùng cột -> nối dọc
        if c["cy"] < p["cy"]:
            ps, cs = "B", "T"
        else:
            ps, cs = "T", "B"
    x1, y1 = anchor(p, ps)
    x2, y2 = anchor(c, cs)
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-", color=REL_C, lw=1.0,
                                connectionstyle="arc3,rad=0.06"), zorder=2)
    # ký hiệu "một" (bar) ở parent, "nhiều" (chấm) ở child
    ax.add_patch(Circle((x2, y2), 0.07, facecolor=REL_C, edgecolor="none", zorder=6))
    # nhãn đặt gần phía parent (t=0.28) để tránh đè lên hộp bảng con
    t = 0.28
    mx, my = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
    ax.text(mx, my + 0.12, label, ha="center", va="center", fontsize=7,
            color=REL_C, style="italic", zorder=6,
            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.85))


def main():
    fig, ax = plt.subplots(figsize=(16, 9.5))
    for name in TABLES:
        draw_table(ax, name)
    for parent, child, label in RELS:
        draw_rel(ax, parent, child, label)
    # chú giải
    ax.text(0.3, 0.9, "PK", color=PK_C, fontsize=9, fontweight="bold", family="monospace")
    ax.text(0.9, 0.9, "= Khóa chính   ", color="#444", fontsize=9, va="center")
    ax.text(3.2, 0.9, "FK", color=FK_C, fontsize=9, fontweight="bold", family="monospace")
    ax.text(3.8, 0.9, "= Khóa ngoại", color="#444", fontsize=9, va="center")
    ax.set_xlim(-0.2, 16.0)
    ax.set_ylim(0.2, 14.2)
    ax.axis("off")
    ax.set_aspect("equal", adjustable="box")
    plt.tight_layout(pad=0.4)
    plt.savefig(OUT, dpi=170, bbox_inches="tight", facecolor="white")
    print("SAVED:", OUT)


if __name__ == "__main__":
    main()
