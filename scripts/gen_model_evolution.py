import matplotlib.pyplot as plt
import numpy as np
import matplotlib

# Use a non-interactive backend
matplotlib.use('Agg')

# Data extraction
models = [
    'v1 (CNN-LSTM)',
    'v22 (TCN+SE)',
    'v25 (ResNet-1D)',
    'v30 (CNN thuần)',
    'v30_tcn (TCN giãn nở)',
    'v30_opt (Đề xuất)'
]

acc = [91.57, 91.56, 91.01, 93.43, 96.02, 95.33]
macro_f1 = [0.9294, 0.9267, 0.9238, 0.9259, 0.9596, 0.9524]
f1_trans = [0.0, 0.8554, 0.8365, 0.7993, 0.9266, 0.9071] # 0.0 means N/A

x = np.arange(len(models))

fig, ax1 = plt.subplots(figsize=(12, 6))

# Plot Accuracy
color = 'tab:blue'
ax1.set_xlabel('Phiên bản mô hình (Model Versions)', fontsize=12)
ax1.set_ylabel('Độ chính xác - Accuracy (%)', color=color, fontsize=12)
line1 = ax1.plot(x, acc, marker='o', color=color, linewidth=2.5, markersize=8, label='Accuracy')
ax1.tick_params(axis='y', labelcolor=color)
ax1.set_xticks(x)
ax1.set_xticklabels(models, rotation=15, ha='right', fontsize=10)
ax1.set_ylim(88, 98)

# Add grid
ax1.grid(True, linestyle='--', alpha=0.6)

# Create a second y-axis for F1 scores
ax2 = ax1.twinx()
color2 = 'tab:orange'
color3 = 'tab:green'
ax2.set_ylabel('Điểm F1 (F1-Score)', color='black', fontsize=12)
line2 = ax2.plot(x, macro_f1, marker='s', color=color2, linewidth=2.5, markersize=8, label='Macro-F1')
# For F1-Trans, we skip v1
x_trans = x[1:]
f1_trans_valid = f1_trans[1:]
line3 = ax2.plot(x_trans, f1_trans_valid, marker='^', color=color3, linewidth=2.5, markersize=8, linestyle='--', label='F1-Trans')
ax2.tick_params(axis='y', labelcolor='black')
ax2.set_ylim(0.75, 1.0)

# Add title
plt.title('Tiến trình tối ưu hóa hiệu năng các phiên bản mô hình', fontsize=14, fontweight='bold', pad=20)

# Add legends
lines = line1 + line2 + line3
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='lower right', framealpha=0.9)

# Add data labels
for i, txt in enumerate(acc):
    ax1.annotate(f"{txt:.2f}%", (x[i], acc[i]), textcoords="offset points", xytext=(0,10), ha='center', fontsize=9, color='blue', fontweight='bold')

for i, txt in enumerate(macro_f1):
    ax2.annotate(f"{txt:.4f}", (x[i], macro_f1[i]), textcoords="offset points", xytext=(0,-15), ha='center', fontsize=9, color='darkorange', fontweight='bold')

for i, txt in enumerate(f1_trans_valid):
    ax2.annotate(f"{txt:.4f}", (x_trans[i], f1_trans_valid[i]), textcoords="offset points", xytext=(0,15), ha='center', fontsize=9, color='green', fontweight='bold')

# Highlight the final proposed model
ax1.axvspan(4.5, 5.5, color='yellow', alpha=0.1)

plt.tight_layout()
plt.savefig('d:/datn/report/Do_an_tot_nghiep_Vu_Manh_Hung/Hinhve/model_evolution.png', dpi=300)
print('Generated model_evolution.png successfully')
