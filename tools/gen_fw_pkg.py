# -*- coding: utf-8 -*-
"""
Sinh sơ đồ gói kiến trúc firmware (fw_pkg.png) bằng matplotlib — tọa độ CỐ ĐỊNH
để mũi tên mạch lạc, không đè nhau / không xuyên hộp.
Bố cục: cặp giao tiếp đặt KỀ NHAU (net–cloud, imu–ai); driver thẳng cột với service
nó nối; luồng NGÃ (đỏ) đi vòng phía trên, không cắt hộp.
Chạy: python gen_fw_pkg.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = r"d:\datn\report\Do_an_tot_nghiep_Vu_Manh_Hung\Hinhve\fw_pkg.png"

EDGE = "#475467"        # viền hộp
GREY = "#667085"        # mũi tên thường
RED = "#C0392B"         # luồng ngã
TXT = "#101828"

# ---- Vị trí hộp: name -> (cx, cy, w, h, "Tên", "phụ đề") ----
BW, BH = 2.5, 1.0
boxes = {
    "sys":   (7.7, 7.7, 3.1, 1.0, "sys_manager", "FSM & Event Loop"),
    "net":   (1.8, 5.05, BW, BH, "svc_network", "Quản lý mạng"),
    "cloud": (4.75, 5.05, BW, BH, "svc_cloud", "Kết nối MQTT"),
    "imu":   (7.7, 5.05, BW, BH, "svc_imu", "Lấy mẫu 100Hz"),
    "ai":    (10.65, 5.05, BW, BH, "svc_ai", "TinyML Fall Detect"),
    "ota":   (13.6, 5.05, BW, BH, "svc_ota", "Cập nhật OTA"),
    "d_sim": (1.8, 2.25, BW, BH, "drv_a7680c", "4G LTE"),
    "d_bat": (4.75, 2.25, BW, BH, "drv_battery", "Theo dõi Pin"),
    "d_mpu": (7.7, 2.25, BW, BH, "drv_mpu6050", "Cảm biến IMU"),
    "l_kal": (10.5, 2.25, BW, BH, "lib_kalman", "Lọc tín hiệu"),
    "l_mod": (12.6, 2.25, 2.0, BH, "lib_model", "Trọng số"),
    "l_tin": (14.6, 2.25, 2.0, BH, "lib_tinyml", "Lõi AI"),
}

# ---- Dải tầng: (x0, y0, x1, y1, nhãn, màu nền) ----
bands = [
    (0.4, 6.85, 16.1, 8.6, "Tầng Hệ thống (System)", "#EDF1F7"),
    (0.4, 4.25, 16.1, 5.95, "Tầng Dịch vụ (Services)", "#EFF4EF"),
    (0.4, 1.45, 9.05, 3.15, "Tầng Điều khiển (Drivers)", "#F8F2E9"),
    (9.2, 1.45, 16.1, 3.15, "Tầng Thư viện (Libraries)", "#F2F0F8"),
]

fig, ax = plt.subplots(figsize=(16.2, 9.2), dpi=150)
ax.set_xlim(0, 16.3); ax.set_ylim(1.2, 9.0); ax.axis("off")

# vẽ dải tầng
for x0, y0, x1, y1, lbl, col in bands:
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0,
                 boxstyle="round,pad=0.02,rounding_size=0.14",
                 linewidth=1.1, edgecolor="#C3CDDD", facecolor=col, zorder=1))
    ax.text(x0 + 0.22, y1 - 0.26, lbl, fontsize=13, fontweight="bold",
            color="#344054", ha="left", va="center", zorder=2)


def draw_box(key):
    cx, cy, w, h, name, sub = boxes[key]
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                 boxstyle="round,pad=0.02,rounding_size=0.10",
                 linewidth=1.3, edgecolor=EDGE, facecolor="white", zorder=3))
    ax.text(cx, cy + 0.16, name, fontsize=12.5, fontweight="bold",
            color=TXT, ha="center", va="center", zorder=4)
    ax.text(cx, cy - 0.20, sub, fontsize=10.5, color="#475467",
            ha="center", va="center", zorder=4)


for k in boxes:
    draw_box(k)


def border(key, tx, ty):
    """Điểm trên biên hộp `key` theo hướng tới (tx,ty)."""
    cx, cy, w, h, *_ = boxes[key]
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (w / 2) / abs(dx) if dx else 1e9
    sy = (h / 2) / abs(dy) if dy else 1e9
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def arrow(a, b, label="", color=GREY, lw=1.4, rad=0.0, lpos=0.5, ldx=0.0, ldy=0.0):
    ax2, ay = boxes[a][0], boxes[a][1]
    bx, by = boxes[b][0], boxes[b][1]
    p0 = border(a, bx, by)
    p1 = border(b, ax2, ay)
    ax.add_patch(FancyArrowPatch(p0, p1, connectionstyle=f"arc3,rad={rad}",
                 arrowstyle="-|>", mutation_scale=16, linewidth=lw,
                 color=color, zorder=5, shrinkA=0, shrinkB=0))
    if label:
        mx = p0[0] + (p1[0] - p0[0]) * lpos + ldx
        my = p0[1] + (p1[1] - p0[1]) * lpos + ldy
        ax.text(mx, my, label, fontsize=10, color=color if color == RED else "#1D2939",
                ha="center", va="center", zorder=6,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9))


# --- luồng dữ liệu thường ---
arrow("d_sim", "net", "UART/PPP", ldx=-0.55, lpos=0.5)   # dọc, nhãn né sang trái
arrow("d_mpu", "imu", "I2C", ldx=-0.35, lpos=0.5)        # dọc
arrow("net", "cloud", "Link up", ldy=-0.62)              # ngang, nhãn hạ xuống dưới
arrow("imu", "ai", "Cấp dữ liệu", ldy=-0.62)             # ngang, nhãn hạ xuống dưới
arrow("imu", "l_kal", "Lọc nhiễu", rad=-0.08, lpos=0.5, ldx=-0.35)  # chéo xuống thư viện
arrow("ai", "l_mod", "Nạp", rad=0.07, lpos=0.5, ldx=0.35)
arrow("ai", "l_tin", "Suy luận", rad=0.13, lpos=0.55, ldy=-0.05)

# --- luồng phát hiện ngã (đỏ, đi vòng phía trên, không cắt hộp) ---
arrow("ai", "sys", "Sự kiện Ngã", color=RED, lw=2.6, rad=0.20, lpos=0.5, ldx=0.5, ldy=0.15)
arrow("sys", "cloud", "Cảnh báo SOS", color=RED, lw=2.6, rad=0.20, lpos=0.5, ldx=-0.55)

plt.savefig(OUT, bbox_inches="tight", pad_inches=0.15, facecolor="white")
print("Saved to", OUT)
