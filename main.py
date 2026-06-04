

import argparse
import time
import cv2
import numpy as np
import json
import os
import sys

# Thêm thư mục src vào path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from detector import VehicleDetector
from counter  import LineCounter
from manager  import ParkingManager
from hud      import draw_hud


def parse_args():
    ap = argparse.ArgumentParser(description="Vehicle Counting System - YOLOv8")
    ap.add_argument("--source",     default="0",          help="Video/image/webcam (0)")
    ap.add_argument("--model",      default="yolov8n.pt", help="YOLO model path")
    ap.add_argument("--conf",       type=float, default=0.4,  help="Confidence threshold")
    ap.add_argument("--iou",        type=float, default=0.45, help="IoU threshold")
    ap.add_argument("--capacity",   type=int,   default=50,   help="Bãi đỗ: sức chứa")
    ap.add_argument("--line-ratio", type=float, default=0.5,  help="Tỉ lệ Y cho counting line")
    ap.add_argument("--output",     default="output/result.mp4", help="Output video path")
    ap.add_argument("--image",      action="store_true",     help="Xử lý ảnh tĩnh (không phải video)")
    ap.add_argument("--no-display", action="store_true",     help="Không hiển thị cửa sổ")
    ap.add_argument("--save-log",   action="store_true",     help="Lưu log JSON")
    return ap.parse_args()


def process_image(args):
    """Xử lý ảnh tĩnh."""
    frame = cv2.imread(args.source)
    if frame is None:
        print(f"[Lỗi] Không thể đọc ảnh: {args.source}")
        return

    h, w = frame.shape[:2]
    line_y = int(h * args.line_ratio)

    detector = VehicleDetector(args.model, args.conf, args.iou)
    counter  = LineCounter(line_y, w)
    manager  = ParkingManager(args.capacity)

    detections = detector.detect(frame)
    counter.update(detections)
    manager.sync_from_counter(counter.total_in(), counter.total_out())

    # Vẽ kết quả
    frame = detector.draw_detections(frame, detections)
    frame = counter.draw(frame)
    frame = draw_hud(frame, manager.get_stats(), counter.get_summary(), fps=0)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    out_path = args.output.replace(".mp4", ".jpg")
    cv2.imwrite(out_path, frame)
    print(f"[✓] Đã lưu kết quả: {out_path}")
    print(f"[i] Phát hiện {len(detections)} xe")

    if not args.no_display:
        cv2.imshow("Vehicle Detection", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def process_video(args):
    """Xử lý video / webcam."""
    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"[Lỗi] Không thể mở nguồn: {args.source}")
        return

    w  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps_src = cap.get(cv2.CAP_PROP_FPS) or 30
    line_y  = int(h * args.line_ratio)

    print(f"[Info] Nguồn: {args.source} | {w}x{h} @ {fps_src:.0f}fps")

    detector = VehicleDetector(args.model, args.conf, args.iou)
    counter  = LineCounter(line_y, w)
    manager  = ParkingManager(args.capacity)

    # Output writer
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(args.output, fourcc, fps_src, (w, h))

    fps_timer = time.time()
    fps_actual = 0.0
    frame_count = 0

    print("[▶] Đang xử lý... Nhấn 'q' để thoát")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Detect & count
        detections = detector.detect(frame)
        new_records = counter.update(detections)

        # Đồng bộ manager
        for rec in new_records:
            if rec.direction == "in":
                manager.vehicle_enter(rec.class_name)
            else:
                manager.vehicle_exit(rec.class_name)

        # Tính FPS thực tế
        frame_count += 1
        elapsed = time.time() - fps_timer
        if elapsed >= 1.0:
            fps_actual = frame_count / elapsed
            frame_count = 0
            fps_timer = time.time()

        # Vẽ
        frame = detector.draw_detections(frame, detections)
        frame = counter.draw(frame)
        frame = draw_hud(frame, manager.get_stats(), counter.get_summary(), fps_actual)

        writer.write(frame)

        if not args.no_display:
            cv2.imshow("Vehicle Counting System - YOLOv8", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("[■] Người dùng thoát")
                break

    cap.release()
    writer.release()
    cv2.destroyAllWindows()

    # In tóm tắt
    stats = manager.get_stats()
    summary = counter.get_summary()
    print("\n" + "=" * 50)
    print("  KẾT QUẢ CUỐI NGÀY")
    print("=" * 50)
    print(f"  Tổng xe vào  : {stats['total_in']}")
    print(f"  Tổng xe ra   : {stats['total_out']}")
    print(f"  Đang trong bãi: {stats['current']}")
    print(f"  Đỉnh cao nhất: {stats['peak']} xe")
    print(f"  Doanh thu    : {stats['revenue_vnd']:,} VND")
    print("=" * 50)
    print(f"  Chi tiết theo loại: {dict(summary['by_type'])}")
    print(f"[✓] Video đã lưu: {args.output}")

    if args.save_log:
        log_path = args.output.replace(".mp4", "_log.json")
        log_data = {
            "stats": stats,
            "summary": {k: v for k, v in summary.items() if k != "by_type"},
            "by_type": {k: dict(v) for k, v in summary["by_type"].items()},
            "events": [
                {"time": e.time, "type": e.event_type, "desc": e.description}
                for e in manager.events[-50:]
            ],
        }
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        print(f"[✓] Log đã lưu: {log_path}")


def main():
    args = parse_args()
    os.makedirs("output", exist_ok=True)

    if args.image:
        process_image(args)
    else:
        process_video(args)


if __name__ == "__main__":
    main()
