"""
red_light_detector.py - Red Light Violation Detection System
Phát hiện xe vượt đèn đỏ
"""

import cv2
import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import time


@dataclass
class RedLightViolation:
    """Bản ghi một lần vi phạm vượt đèn đỏ"""
    timestamp: str
    track_id: int
    vehicle_type: str
    frame_number: int
    violation_severity: str  # "MINOR", "MODERATE", "SEVERE"
    frame_image: Optional[np.ndarray] = None  # Frame snapshot của xe vi phạm
    frame_path: Optional[str] = None  # Đường dẫn ảnh lưu trữ


class RedLightDetector:
    """
    Phát hiện xe vượt đèn đỏ.

    Nguyên lý:
        - Xác định trạng thái đèn (RED, YELLOW, GREEN) dựa trên video
        - Theo dõi xe vượt qua line khi đèn đỏ
        - Tính mức độ vi phạm dựa trên tốc độ và thời gian

    Args:
        detection_line_y: Toạ độ Y của đường phát hiện
        frame_width: Chiều rộng frame
        frame_height: Chiều cao frame
    """

    def __init__(self, detection_line_y: int, frame_width: int, frame_height: int):
        self.detection_line_y = detection_line_y
        self.frame_width = frame_width
        self.frame_height = frame_height

        # Trạng thái đèn giao thông
        self.traffic_light_status = "GREEN"  # RED, YELLOW, GREEN
        self._light_change_time = time.time()
        self._light_duration = 5  # Mỗi trạng thái 5 giây

        # Lịch sử vị trí xe để tính tốc độ
        self._vehicle_positions: Dict[int, deque] = defaultdict(
            lambda: deque(maxlen=30)
        )

        # Vi phạm được ghi nhận
        self.violations: List[RedLightViolation] = []
        self._violation_vehicles = set()  # Tránh ghi nhận lặp

        # Thống kê
        self.total_violations = 0
        self.violation_stats = defaultdict(int)

    def set_light_status(self, status: str):
        """
        Đặt trạng thái đèn giao thông.

        Args:
            status: "RED", "YELLOW", hoặc "GREEN"
        """
        if status in ["RED", "YELLOW", "GREEN"]:
            self.traffic_light_status = status
            self._light_change_time = time.time()

    def set_detection_line_y(self, line_y: int):
        """
        Cập nhật vị trí đường phát hiện vi phạm.
        
        Args:
            line_y: Toạ độ Y mới của đường phát hiện
        """
        self.detection_line_y = max(0, min(line_y, self.frame_height))
    
    def set_detection_line_ratio(self, ratio: float):
        """
        Cập nhật vị trí đường phát hiện vi phạm dựa trên tỉ lệ.
        
        Args:
            ratio: Tỉ lệ Y (0-1) từ trên xuống
        """
        ratio = max(0.1, min(ratio, 0.9))  # Giới hạn từ 0.1 đến 0.9
        line_y = int(self.frame_height * ratio)
        self.set_detection_line_y(line_y)

    def update_light_status_auto(self, frame_count: int, fps: float = 30.0):
        """
        Tự động cập nhật trạng thái đèn theo thời gian.

        Chu kỳ: GREEN (10s) → YELLOW (3s) → RED (10s) → ...

        Args:
            frame_count: Frame hiện tại
            fps: FPS của video
        """
        if fps <= 0:
            return

        elapsed_sec = frame_count / fps
        cycle = elapsed_sec % 23  # Chu kỳ 23 giây (10+3+10)

        if cycle < 10:
            self.traffic_light_status = "GREEN"
        elif cycle < 13:
            self.traffic_light_status = "YELLOW"
        else:
            self.traffic_light_status = "RED"

    def get_vehicle_speed(
        self, track_id: int, center_y: int, fps: float = 30.0
    ) -> float:
        """
        Tính tốc độ xe dựa trên thay đổi vị trí.

        Returns:
            Tốc độ tương đối (pixels/frame)
        """
        if track_id not in self._vehicle_positions:
            self._vehicle_positions[track_id].append(center_y)
            return 0.0

        positions = self._vehicle_positions[track_id]
        if len(positions) < 2:
            positions.append(center_y)
            return 0.0

        # Tính chênh lệch vị trí gần đây
        recent = list(positions)[-5:]  # 5 frame gần đây
        if len(recent) < 2:
            return 0.0

        distance = abs(recent[-1] - recent[0])
        frames_count = len(recent) - 1
        speed = distance / frames_count if frames_count > 0 else 0

        positions.append(center_y)
        return speed

    def detect_violation(
        self,
        detections,
        frame_number: int,
        fps: float = 30.0,
        frame: Optional[np.ndarray] = None,
    ) -> List[RedLightViolation]:
        """
        Phát hiện xe vượt đèn đỏ.

        Args:
            detections: Danh sách detection từ YOLOv8
            frame_number: Frame hiện tại
            fps: FPS video
            frame: Frame hiện tại (để lưu snapshot)

        Returns:
            Danh sách vi phạm mới
        """
        new_violations = []

        for det in detections:
            track_id = det.track_id
            cy = det.center[1]
            class_name = det.class_name

            # Kiểm tra nếu xe vượt qua đường
            # Nếu xe ở dưới đường phát hiện → ghi nhận (bất kể đèn xanh hay đỏ)
            # Để phát hiện tất cả vi phạm, không chỉ khi đèn đỏ
            if cy >= self.detection_line_y and track_id not in self._violation_vehicles:
                # Tính tốc độ xe
                speed = self.get_vehicle_speed(track_id, cy, fps)

                # Tính mức độ vi phạm dựa trên tốc độ
                if speed > 15:  # Tốc độ cao
                    severity = "SEVERE"
                elif speed > 8:  # Tốc độ trung bình
                    severity = "MODERATE"
                else:  # Tốc độ thấp
                    severity = "MINOR"
                
                # Nếu không ở trong trạng thái RED, giảm mức độ severity
                # để phân biệt vi phạm thực sự (RED) vs. lưu lượng bình thường (GREEN/YELLOW)
                if self.traffic_light_status != "RED":
                    if severity == "SEVERE":
                        severity = "MODERATE"
                    elif severity == "MODERATE":
                        severity = "MINOR"

                # Crop frame để lưu snapshot của xe
                frame_snapshot = None
                if frame is not None:
                    x1, y1, x2, y2 = det.bbox
                    # Mở rộng bbox một chút để lấy ngữ cảnh
                    x1 = max(0, x1 - 10)
                    y1 = max(0, y1 - 10)
                    x2 = min(frame.shape[1], x2 + 10)
                    y2 = min(frame.shape[0], y2 + 10)
                    frame_snapshot = frame[y1:y2, x1:x2].copy()

                violation = RedLightViolation(
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                    track_id=track_id,
                    vehicle_type=class_name,
                    frame_number=frame_number,
                    violation_severity=severity,
                    frame_image=frame_snapshot,
                )

                self.violations.append(violation)
                self._violation_vehicles.add(track_id)
                self.total_violations += 1
                self.violation_stats[severity] += 1

                new_violations.append(violation)

        return new_violations

    def get_violation_summary(self) -> Dict:
        """Lấy tóm tắt thông tin vi phạm"""
        return {
            "total_violations": self.total_violations,
            "severe_violations": self.violation_stats.get("SEVERE", 0),
            "moderate_violations": self.violation_stats.get("MODERATE", 0),
            "minor_violations": self.violation_stats.get("MINOR", 0),
            "current_light_status": self.traffic_light_status,
            "violations_by_type": dict(
                {
                    det.vehicle_type: sum(
                        1 for v in self.violations if v.vehicle_type == det.vehicle_type
                    )
                    for det in self.violations
                }
            ),
        }

    def draw_light_indicator(self, frame: np.ndarray) -> np.ndarray:
        """Vẽ biểu tượng trạng thái đèn lên frame"""
        light_colors = {
            "RED": (0, 0, 255),      # BGR: Red
            "YELLOW": (0, 220, 255), # BGR: Yellow
            "GREEN": (0, 255, 0),    # BGR: Green
        }

        color = light_colors.get(self.traffic_light_status, (200, 200, 200))

        # Vẽ hình tròn biểu thị đèn
        center = (100, 50)
        radius = 20
        cv2.circle(frame, center, radius, color, -1)

        # Vẽ viền
        cv2.circle(frame, center, radius, (0, 0, 0), 2)

        # Nhãn
        cv2.putText(
            frame,
            f"LIGHT: {self.traffic_light_status}",
            (130, 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
            cv2.LINE_AA,
        )

        return frame

    def draw_violations(self, frame: np.ndarray) -> np.ndarray:
        """Vẽ thông tin vi phạm lên frame"""
        summary = self.get_violation_summary()

        # Panel thông tin vi phạm
        y_offset = 100
        cv2.putText(
            frame,
            f"Red Light Violations: {summary['total_violations']}",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )

        y_offset += 30
        cv2.putText(
            frame,
            f"SEVERE: {summary['severe_violations']} | MODERATE: {summary['moderate_violations']} | MINOR: {summary['minor_violations']}",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 100, 255),
            1,
            cv2.LINE_AA,
        )

        return frame

    def draw_detection_line(self, frame: np.ndarray) -> np.ndarray:
        """
        Vẽ đường phát hiện vi phạm lên frame.
        
        Args:
            frame: Frame để vẽ
            
        Returns:
            Frame với đường đã vẽ
        """
        # Vẽ đường ngang ở vị trí phát hiện
        line_color = (0, 255, 255)  # BGR: Cyan
        line_thickness = 2
        
        # Vẽ đường chính
        cv2.line(
            frame,
            (0, self.detection_line_y),
            (self.frame_width, self.detection_line_y),
            line_color,
            line_thickness
        )
        
        # Vẽ các dấu chỉ thị trên đường
        tick_spacing = 100  # Khoảng cách giữa các dấu
        tick_height = 10
        for x in range(0, self.frame_width, tick_spacing):
            cv2.line(
                frame,
                (x, self.detection_line_y - tick_height),
                (x, self.detection_line_y + tick_height),
                line_color,
                1
            )
        
        # Nhãn hiển thị vị trí đường
        label_text = f"Detection Line: Y={self.detection_line_y}px"
        cv2.putText(
            frame,
            label_text,
            (10, self.detection_line_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            line_color,
            2,
            cv2.LINE_AA
        )
        
        return frame

    def get_recent_violations(self, limit: int = 5) -> List[Dict]:
        """Lấy các vi phạm gần đây nhất"""
        import base64
        recent = self.violations[-limit:]
        violations_list = []
        
        for v in recent:
            violation_dict = {
                "timestamp": v.timestamp,
                "track_id": v.track_id,
                "vehicle_type": v.vehicle_type,
                "severity": v.violation_severity,
                "frame": v.frame_number,
            }
            
            # Chuyển frame_image (numpy array) thành base64 data URL
            if v.frame_image is not None:
                try:
                    # Encode numpy array thành JPEG
                    success, buffer = cv2.imencode('.jpg', v.frame_image)
                    if success:
                        # Chuyển sang base64
                        img_base64 = base64.b64encode(buffer).decode('utf-8')
                        violation_dict['image_path'] = f"data:image/jpeg;base64,{img_base64}"
                    else:
                        violation_dict['image_path'] = None
                except Exception as e:
                    print(f"Error encoding image: {e}")
                    violation_dict['image_path'] = None
            else:
                violation_dict['image_path'] = None
            
            violations_list.append(violation_dict)
        
        return violations_list

    def reset(self):
        """Reset trạng thái để xử lý video mới"""
        self.violations.clear()
        self._violation_vehicles.clear()
        self.total_violations = 0
        self.violation_stats.clear()
        self._vehicle_positions.clear()
        self.traffic_light_status = "GREEN"
