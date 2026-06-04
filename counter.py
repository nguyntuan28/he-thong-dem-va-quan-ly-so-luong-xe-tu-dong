"""
counter.py - Vehicle Flow Monitor
Giám sát lưu lượng xe và tính toán metrics giao thông
"""

import cv2
import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import time


@dataclass
class CountRecord:
    """Bản ghi mỗi lần xe được đếm"""
    timestamp:  str
    track_id:   int
    class_name: str
    direction:  str  # "in" | "out"


class LineCounter:
    """
    Giám sát lưu lượng xe vượt qua một đường.

    Tính năng:
        - Đếm xe vào/ra
        - Tính lưu lượng (xe/phút)
        - Theo dõi mật độ xe
        - Phát hiện kẹt xe
        - Lưu lịch sử lưu lượng theo thời gian

    Args:
        line_y:     Toạ độ Y của đường đếm (pixel)
        frame_w:    Chiều rộng frame (để vẽ đường ngang)
        offset:     Vùng buffer quanh đường (pixel) tránh đếm nhầm
    """

    def __init__(self, line_y: int, frame_w: int, offset: int = 6):
        self.line_y  = line_y
        self.frame_w = frame_w
        self.offset  = offset

        # Lịch sử vị trí Y của từng xe
        self._prev_y: Dict[int, int] = {}

        # Đếm theo loại xe & chiều
        self.counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {"in": 0, "out": 0})
        self.records: List[CountRecord] = []
        
        # Lưu lượng xe - lịch sử theo thời gian
        self.flow_history: deque = deque(maxlen=3600)  # Giữ 1 giờ dữ liệu
        self._last_flow_time = time.time()
        self._frame_count_since_last = 0
        self.current_flow_rate = 0.0  # xe/phút

    # ------------------------------------------------------------------
    def update(self, detections) -> List[CountRecord]:
        """
        Cập nhật đếm với danh sách Detection của frame hiện tại.
        Tính toán lưu lượng xe và các metrics.

        Returns:
            Danh sách CountRecord MỚI trong frame này
        """
        new_records = []
        new_count = 0

        for det in detections:
            tid  = det.track_id
            cy   = det.center[1]
            name = det.class_name

            if tid in self._prev_y:
                prev = self._prev_y[tid]

                crossed_down = prev < self.line_y - self.offset and cy >= self.line_y
                crossed_up   = prev > self.line_y + self.offset and cy <= self.line_y

                if crossed_down:
                    direction = "in"
                    self.counts[name]["in"] += 1
                    new_count += 1
                    rec = CountRecord(
                        timestamp=datetime.now().strftime("%H:%M:%S"),
                        track_id=tid,
                        class_name=name,
                        direction=direction,
                    )
                    self.records.append(rec)
                    new_records.append(rec)

                elif crossed_up:
                    direction = "out"
                    self.counts[name]["out"] += 1
                    new_count += 1
                    rec = CountRecord(
                        timestamp=datetime.now().strftime("%H:%M:%S"),
                        track_id=tid,
                        class_name=name,
                        direction=direction,
                    )
                    self.records.append(rec)
                    new_records.append(rec)

            self._prev_y[tid] = cy

        # Dọn dẹp track_id không còn xuất hiện
        active_ids = {d.track_id for d in detections}
        stale = [tid for tid in self._prev_y if tid not in active_ids]
        for tid in stale:
            del self._prev_y[tid]

        # Cập nhật lưu lượng
        self._frame_count_since_last += 1
        current_time = time.time()
        elapsed = current_time - self._last_flow_time

        # Tính lưu lượng mỗi 10 frames
        if self._frame_count_since_last >= 10 and elapsed > 0:
            # Lưu lượng xe/giây -> xe/phút
            vehicles_per_sec = new_count / (self._frame_count_since_last / 30.0)  # Giả sử 30 FPS
            flow_rate = vehicles_per_sec * 60  # Chuyển sang xe/phút
            
            self.current_flow_rate = flow_rate
            self.flow_history.append({
                'timestamp': datetime.now(),
                'flow_rate': flow_rate,
                'vehicle_count': new_count
            })
            
            self._frame_count_since_last = 0
            self._last_flow_time = current_time

        return new_records

    # ------------------------------------------------------------------
    def total_in(self) -> int:
        return sum(v["in"]  for v in self.counts.values())

    def total_out(self) -> int:
        return sum(v["out"] for v in self.counts.values())

    def current_inside(self) -> int:
        return max(0, self.total_in() - self.total_out())

    def get_flow_rate(self) -> float:
        """Lấy lưu lượng xe hiện tại (xe/phút)"""
        return self.current_flow_rate

    def get_average_flow_rate(self, seconds: int = 60) -> float:
        """Tính lưu lượng trung bình trong N giây gần đây"""
        if not self.flow_history:
            return 0.0
        
        now = datetime.now()
        cutoff = now - timedelta(seconds=seconds)
        
        recent = [f for f in self.flow_history if f['timestamp'] >= cutoff]
        if not recent:
            return 0.0
        
        return sum(f['flow_rate'] for f in recent) / len(recent)

    def get_peak_flow_rate(self, seconds: int = 60) -> float:
        """Lấy lưu lượng cao nhất trong N giây gần đây"""
        if not self.flow_history:
            return 0.0
        
        now = datetime.now()
        cutoff = now - timedelta(seconds=seconds)
        
        recent = [f for f in self.flow_history if f['timestamp'] >= cutoff]
        if not recent:
            return 0.0
        
        return max(f['flow_rate'] for f in recent)

    def get_traffic_density(self, detections) -> float:
        """Tính mật độ xe (0-100%)"""
        if len(detections) == 0:
            return 0.0
        
        # Tính % chiều rộng frame bị chiếm bởi xe
        total_width = sum(d.bbox[2] - d.bbox[0] for d in detections)
        density = (total_width / (self.frame_w * len(detections))) * 100
        return min(100.0, density)

    def get_congestion_level(self, detections) -> str:
        """Phát hiện mức độ kẹt xe"""
        density = self.get_traffic_density(detections)
        flow_rate = self.get_flow_rate()
        vehicle_count = len(detections)
        
        # Khống chế dựa trên mật độ và số lượng xe
        if flow_rate < 5 and vehicle_count > 20:
            return "VERY_HEAVY"  # Rất kẹt
        elif density > 70 or vehicle_count > 15:
            return "HEAVY"  # Kẹt
        elif density > 40 or vehicle_count > 8:
            return "MODERATE"  # Vừa
        elif density > 20:
            return "LIGHT"  # Nhẹ
        else:
            return "FREE"  # Thông thoáng

    def get_summary(self) -> Dict:
        return {
            "total_in":       self.total_in(),
            "total_out":      self.total_out(),
            "current_inside": self.current_inside(),
            "by_type":        dict(self.counts),
            "flow_rate":      self.get_flow_rate(),
            "avg_flow_60s":   self.get_average_flow_rate(60),
            "peak_flow_60s":  self.get_peak_flow_rate(60),
        }

    # ------------------------------------------------------------------
    def draw(self, frame: np.ndarray, detections=None) -> np.ndarray:
        """Vẽ thông tin lưu lượng lên frame (không vẽ đường)."""
        lw = self.frame_w

        # Thông tin lưu lượng
        cv2.putText(
            frame, f"FLOW MONITORING - {self.get_flow_rate():.1f} vehicles/min",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 255), 1, cv2.LINE_AA,
        )

        # Mức độ kẹt xe
        if detections:
            congestion = self.get_congestion_level(detections)
            congestion_colors = {
                "FREE": (0, 220, 0),        # Xanh
                "LIGHT": (0, 220, 255),    # Vàng
                "MODERATE": (0, 165, 255), # Cam
                "HEAVY": (0, 100, 255),    # Đỏ cam
                "VERY_HEAVY": (0, 0, 255)  # Đỏ
            }
            color = congestion_colors.get(congestion, (200, 200, 200))
            cv2.putText(frame, f"Congestion: {congestion}", 
                       (lw - 300, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA)

        return frame
