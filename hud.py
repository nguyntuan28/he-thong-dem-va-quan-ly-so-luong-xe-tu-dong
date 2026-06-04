"""
hud.py - Heads-Up Display overlay
Vẽ thông tin thống kê lên frame theo thời gian thực
"""

import cv2
import numpy as np
from datetime import datetime
from typing import Dict


# Màu sắc chủ đề
C_BG      = (15,  15,  25)   # nền tối
C_TEXT    = (230, 230, 230)  # chữ trắng
C_GREEN   = (0,   220, 120)  # OK / IN
C_RED     = (60,  80,  255)  # cảnh báo / OUT
C_YELLOW  = (0,   210, 255)  # nhấn mạnh
C_BLUE    = (255, 160, 50)   # xe tải / bus

STATUS_COLORS = {
    "Còn chỗ":  C_GREEN,
    "Sắp đầy":  C_YELLOW,
    "Đầy":      C_RED,
    "Quá tải":  (0, 0, 255),
}


def _draw_panel(frame, x, y, w, h, alpha=0.65):
    """Vẽ panel mờ (semi-transparent)."""
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), C_BG, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    cv2.rectangle(frame, (x, y), (x + w, y + h), (60, 60, 80), 1)


def _put(frame, text, x, y, scale=0.55, color=C_TEXT, bold=False):
    thickness = 2 if bold else 1
    cv2.putText(frame, text, (x, y),
                cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def draw_hud(
    frame:      np.ndarray,
    stats:      Dict,
    counter_summary: Dict,
    fps:        float = 0.0,
) -> np.ndarray:
    """
    Vẽ toàn bộ HUD lên frame.

    Args:
        frame:           Frame gốc
        stats:           Kết quả từ ParkingManager.get_stats()
        counter_summary: Kết quả từ LineCounter.get_summary()
        fps:             FPS thực tế
    """
    h, w = frame.shape[:2]

    # ── Panel trái trên: Bãi đỗ xe ─────────────────────────────────────
    px, py, pw, ph = 10, 10, 260, 185
    _draw_panel(frame, px, py, pw, ph)

    _put(frame, "BAI DO XE TU DONG", px+10, py+22, 0.52, C_YELLOW, bold=True)
    cv2.line(frame, (px+10, py+28), (px+pw-10, py+28), (60, 60, 90), 1)

    status      = stats.get("status", "N/A")
    st_color    = STATUS_COLORS.get(status, C_TEXT)
    current     = stats.get("current", 0)
    capacity    = stats.get("capacity", 0)
    occupancy   = stats.get("occupancy", 0)
    available   = stats.get("available", 0)

    _put(frame, f"Trang thai: {status}", px+10, py+50, 0.5, st_color, bold=True)
    _put(frame, f"Dang do:  {current} / {capacity} xe", px+10, py+72, 0.5)
    _put(frame, f"Con trong: {available} cho",           px+10, py+92, 0.5, C_GREEN)

    # Thanh tiến trình chiếm dụng
    bar_x, bar_y, bar_w, bar_h = px+10, py+104, pw-20, 14
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x+bar_w, bar_y+bar_h), (50,50,70), -1)
    fill = int(bar_w * min(occupancy/100, 1.0))
    bar_color = st_color
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x+fill, bar_y+bar_h), bar_color, -1)
    _put(frame, f"{occupancy:.0f}%", bar_x + bar_w//2 - 12, bar_y+11, 0.4, (0,0,0), bold=True)

    _put(frame, f"Tong vao:  {stats.get('total_in',0)} xe",  px+10, py+134, 0.48, C_GREEN)
    _put(frame, f"Tong ra:   {stats.get('total_out',0)} xe", px+10, py+154, 0.48, C_RED)
    rev = stats.get("revenue_vnd", 0)
    _put(frame, f"Doanh thu: {rev:,} VND", px+10, py+174, 0.44, C_YELLOW)

    # ── Panel phải trên: Thống kê theo loại xe ─────────────────────────
    px2, py2, pw2, ph2 = w - 210, 10, 200, 170
    _draw_panel(frame, px2, py2, pw2, ph2)

    _put(frame, "THONG KE LOAI XE", px2+10, py2+22, 0.5, C_YELLOW, bold=True)
    cv2.line(frame, (px2+10, py2+28), (px2+pw2-10, py2+28), (60, 60, 90), 1)

    by_type = counter_summary.get("by_type", {})
    type_colors = {
        "car":        C_GREEN,
        "motorcycle": (0, 200, 255),
        "bus":        C_BLUE,
        "truck":      (50, 150, 255),
        "bicycle":    (200, 100, 255),
    }
    label_vi = {
        "car": "Xe hoi", "motorcycle": "Xe may",
        "bus": "Xe buyt", "truck": "Xe tai", "bicycle": "Xe dap",
    }

    row = py2 + 48
    if by_type:
        for vtype, cnts in by_type.items():
            col = type_colors.get(vtype, C_TEXT)
            lbl = label_vi.get(vtype, vtype)
            total = cnts.get("in", 0) + cnts.get("out", 0)
            _put(frame, f"{lbl}: {total} xe  (+{cnts.get('in',0)} -{cnts.get('out',0)})",
                 px2+10, row, 0.42, col)
            row += 20
    else:
        _put(frame, "Chua phat hien xe", px2+10, row, 0.44, (120, 120, 120))
        row += 20

    # Tổng IN / OUT từ counter
    row = max(row, py2 + 130)
    _put(frame, f"IN :{counter_summary.get('total_in',0):>4}  OUT:{counter_summary.get('total_out',0):>4}",
         px2+10, row, 0.45, C_TEXT)
    _put(frame, f"Trong bai: {counter_summary.get('current_inside',0)} xe",
         px2+10, row+20, 0.45, C_GREEN)

    # ── Dải thông tin dưới: FPS + thời gian ────────────────────────────
    now = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
    info = f"FPS: {fps:5.1f}  |  {now}  |  YOLOv8 Vehicle Counter"
    _put(frame, info, 12, h - 10, 0.45, (150, 150, 160))

    # ── Cảnh báo nổi bật (nếu bãi đầy) ───────────────────────────────
    if status in ("Đầy", "Quá tải"):
        alert = "!! BAI DAY - KHONG CON CHO ĐO !!"
        tw, _ = cv2.getTextSize(alert, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0], None
        ax = (w - tw[0]) // 2 if isinstance(tw, tuple) else w // 4
        # Flash effect via seconds parity
        if datetime.now().second % 2 == 0:
            cv2.putText(frame, alert, (ax, h - 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)

    return frame
