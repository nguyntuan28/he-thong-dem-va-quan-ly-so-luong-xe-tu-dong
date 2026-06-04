"""
demo.py - Demo nội bộ (không cần camera/video thật)
Sinh dữ liệu giả lập để kiểm thử toàn bộ pipeline
"""

import cv2
import numpy as np
import sys, os, random, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from counter import LineCounter, Detection
from manager import ParkingManager
from hud     import draw_hud


# ─── Fake vehicle simulator ─────────────────────────────────────────────────
VEHICLE_TYPES = ["car", "motorcycle", "bus", "truck", "bicycle"]
COLORS_BGR    = {
    "car":        (0, 200, 255),
    "motorcycle": (0, 255, 150),
    "bus":        (255, 120, 0),
    "truck":      (80,  80, 255),
    "bicycle":    (220, 50, 255),
}

class FakeVehicle:
    _next_id = 1

    def __init__(self, frame_w, frame_h):
        self.tid   = FakeVehicle._next_id; FakeVehicle._next_id += 1
        self.vtype = random.choice(VEHICLE_TYPES)
        self.w     = {"car": 70, "motorcycle": 35, "bus": 100, "truck": 90, "bicycle": 28}[self.vtype]
        self.h_box = {"car": 45, "motorcycle": 25, "bus":  70, "truck":  60, "bicycle": 40}[self.vtype]
        self.x     = random.randint(50, frame_w - 100)
        self.y     = random.randint(-self.h_box - 10, -self.h_box)
        self.speed = random.uniform(3, 8)
        self.fw    = frame_w
        self.fh    = frame_h
        self.conf  = random.uniform(0.72, 0.98)

    def update(self):
        self.y += self.speed

    def is_offscreen(self):
        return self.y > self.fh + 20

    def to_detection(self) -> Detection:
        cx, cy = self.x + self.w // 2, self.y + self.h_box // 2
        return Detection(
            track_id=self.tid,
            class_id=2,
            class_name=self.vtype,
            confidence=self.conf,
            bbox=(self.x, self.y, self.x + self.w, self.y + self.h_box),
            center=(cx, cy),
        )

    def draw(self, frame):
        color = COLORS_BGR[self.vtype]
        x1, y1, x2, y2 = self.x, self.y, self.x + self.w, self.y + self.h_box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        lbl = f"#{self.tid} {self.vtype} {self.conf:.0%}"
        cv2.putText(frame, lbl, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1, cv2.LINE_AA)
        cv2.circle(frame, (self.x + self.w//2, self.y + self.h_box//2), 4, color, -1)


# ─── Main demo loop ──────────────────────────────────────────────────────────
def run_demo(
    frame_w: int  = 960,
    frame_h: int  = 540,
    capacity: int = 30,
    duration_s: float = 30,
    out_path: str = "output/demo_result.mp4",
    show: bool = True,
):
    os.makedirs("output", exist_ok=True)
    line_y  = int(frame_h * 0.5)
    counter = LineCounter(line_y, frame_w)
    manager = ParkingManager(capacity)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, 20, (frame_w, frame_h))

    vehicles = []
    spawn_timer = 0
    fps_timer   = time.time()
    fps_val     = 20.0
    frame_count = 0
    t_start     = time.time()

    # Lưu ảnh snapshot frames
    snapshot_frames = []

    print(f"[Demo] Đang chạy demo {duration_s:.0f}s — {frame_w}x{frame_h} ...")

    while True:
        elapsed = time.time() - t_start
        if elapsed > duration_s:
            break

        # Tạo nền giả bãi đỗ xe
        frame = np.zeros((frame_h, frame_w, 3), dtype=np.uint8)
        frame[:] = (20, 25, 30)

        # Lưới đường kẻ nền
        for gx in range(0, frame_w, 80):
            cv2.line(frame, (gx, 0), (gx, frame_h), (30, 35, 42), 1)
        for gy in range(0, frame_h, 60):
            cv2.line(frame, (0, gy), (frame_w, gy), (30, 35, 42), 1)

        # Spawn xe mới
        spawn_timer += 1
        spawn_interval = random.randint(18, 35)
        if spawn_timer >= spawn_interval:
            vehicles.append(FakeVehicle(frame_w, frame_h))
            spawn_timer = 0

        # Cập nhật & vẽ xe
        active = []
        for v in vehicles:
            v.update()
            if not v.is_offscreen():
                active.append(v)
                v.draw(frame)
        vehicles = active

        # Đếm
        detections = [v.to_detection() for v in vehicles]
        new_recs   = counter.update(detections)
        for rec in new_recs:
            if rec.direction == "in":
                manager.vehicle_enter(rec.class_name)
            else:
                manager.vehicle_exit(rec.class_name)

        # Vẽ đường đếm & HUD
        counter.draw(frame)

        # FPS
        frame_count += 1
        if time.time() - fps_timer >= 1.0:
            fps_val     = frame_count / (time.time() - fps_timer)
            frame_count = 0
            fps_timer   = time.time()

        frame = draw_hud(frame, manager.get_stats(), counter.get_summary(), fps_val)

        # Thanh thời gian
        prog = elapsed / duration_s
        cv2.rectangle(frame, (0, frame_h - 4), (frame_w, frame_h), (40,40,40), -1)
        cv2.rectangle(frame, (0, frame_h - 4), (int(frame_w * prog), frame_h), (0, 180, 255), -1)

        writer.write(frame)
        if elapsed in (5, 10, 15, 20, 25) or len(snapshot_frames) == 0:
            snapshot_frames.append(frame.copy())

        if show:
            cv2.imshow("Vehicle Counting Demo - YOLOv8 Simulation", frame)
            key = cv2.waitKey(int(1000 / 20))
            if key & 0xFF == ord("q"):
                break

    writer.release()
    cv2.destroyAllWindows()

    # Lưu ảnh snapshot
    for i, sf in enumerate(snapshot_frames[:3]):
        cv2.imwrite(f"output/snapshot_{i+1}.jpg", sf)

    stats = manager.get_stats()
    print("\n" + "=" * 52)
    print("  DEMO KẾT THÚC — BÁO CÁO")
    print("=" * 52)
    print(f"  Xe vào     : {stats['total_in']}")
    print(f"  Xe ra      : {stats['total_out']}")
    print(f"  Còn trong  : {stats['current']}")
    print(f"  Đỉnh cao   : {stats['peak']} xe")
    print(f"  Tỉ lệ      : {stats['occupancy']}%")
    print(f"  Doanh thu  : {stats['revenue_vnd']:,} VND")
    print(f"  Video lưu  : {out_path}")
    print("=" * 52)

    return stats, out_path


if __name__ == "__main__":
    run_demo(show=True, duration_s=30)
