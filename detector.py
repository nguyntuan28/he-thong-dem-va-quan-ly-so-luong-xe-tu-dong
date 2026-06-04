"""
detector.py - YOLOv8 Vehicle Detector
Phát hiện xe cộ sử dụng YOLOv8
"""

import cv2
import numpy as np
from ultralytics import YOLO
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


# COCO class IDs for vehicles
VEHICLE_CLASSES = {
    2:  "car",        # xe hơi
    3:  "motorcycle", # xe máy
    5:  "bus",        # xe buýt
    7:  "truck",      # xe tải
    1:  "bicycle",    # xe đạp
}

# Color map for each vehicle type (BGR)
CLASS_COLORS = {
    "car":        (0, 200, 255),
    "motorcycle": (0, 255, 128),
    "bus":        (255, 100, 0),
    "truck":      (255, 0, 100),
    "bicycle":    (200, 0, 255),
}


@dataclass
class Detection:
    """Lưu trữ thông tin một lần phát hiện xe"""
    track_id:   int
    class_id:   int
    class_name: str
    confidence: float
    bbox:       Tuple[int, int, int, int]  # x1, y1, x2, y2
    center:     Tuple[int, int]            # cx, cy


class VehicleDetector:
    """
    Phát hiện và theo dõi xe cộ sử dụng YOLOv8.

    Args:
        model_path: Đường dẫn đến model YOLO (mặc định: yolov8n.pt)
        confidence: Ngưỡng tin cậy tối thiểu (0-1)
        iou:        Ngưỡng IoU cho NMS
        device:     Thiết bị tính toán ('cpu', '0', '0,1', ...)
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence: float = 0.4,
        iou: float = 0.45,
        device: str = "cpu",
    ):
        print(f"[Detector] Đang tải model: {model_path}")
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.iou = iou
        self.device = device
        print("[Detector] Model sẵn sàng ✓")

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Phát hiện xe trong một frame.

        Args:
            frame: Ảnh BGR (numpy array)

        Returns:
            Danh sách các Detection
        """
        results = self.model.track(
            frame,
            persist=True,
            conf=self.confidence,
            iou=self.iou,
            device=self.device,
            classes=list(VEHICLE_CLASSES.keys()),
            verbose=False,
        )

        detections: List[Detection] = []

        if results[0].boxes is None:
            return detections

        boxes = results[0].boxes
        for box in boxes:
            cls_id = int(box.cls[0])
            if cls_id not in VEHICLE_CLASSES:
                continue

            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            track_id = int(box.id[0]) if box.id is not None else -1

            detections.append(Detection(
                track_id=track_id,
                class_id=cls_id,
                class_name=VEHICLE_CLASSES[cls_id],
                confidence=conf,
                bbox=(x1, y1, x2, y2),
                center=(cx, cy),
            ))

        return detections

    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Detection],
        show_conf: bool = True,
    ) -> np.ndarray:
        """Vẽ bounding box và nhãn lên frame."""
        output = frame.copy()

        for det in detections:
            color = CLASS_COLORS.get(det.class_name, (0, 255, 0))
            x1, y1, x2, y2 = det.bbox

            # Bounding box
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)

            # Label background
            label = f"#{det.track_id} {det.class_name}"
            if show_conf:
                label += f" {det.confidence:.0%}"

            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.rectangle(output, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
            cv2.putText(
                output, label, (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA,
            )

            # Center dot
            cv2.circle(output, det.center, 4, color, -1)

        return output
