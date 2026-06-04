"""
manager.py - Parking Lot Manager
Quản lý bãi đỗ xe: sức chứa, trạng thái, cảnh báo
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class LotStatus(Enum):
    AVAILABLE = "Còn chỗ"
    ALMOST_FULL = "Sắp đầy"
    FULL = "Đầy"
    OVERFLOW = "Quá tải"


@dataclass
class ParkingEvent:
    time: str
    event_type: str   # "ENTER" | "EXIT" | "ALERT"
    description: str
    vehicle_type: Optional[str] = None


class ParkingManager:
    """
    Quản lý trạng thái bãi đỗ xe.

    Args:
        capacity:    Sức chứa tối đa (số xe)
        alert_ratio: Tỉ lệ kích hoạt cảnh báo gần đầy (mặc định 0.85)
    """

    def __init__(self, capacity: int = 50, alert_ratio: float = 0.85):
        self.capacity    = capacity
        self.alert_ratio = alert_ratio

        self.current     = 0       # xe đang trong bãi
        self.total_in    = 0       # tổng vào từ đầu ngày
        self.total_out   = 0       # tổng ra từ đầu ngày
        self.peak        = 0       # đỉnh cao nhất trong ngày

        self.events: List[ParkingEvent] = []
        self._revenue: float = 0.0          # doanh thu (ví dụ: 5000 VND/lượt)
        self.fee_per_vehicle: float = 5000  # VND

    # ------------------------------------------------------------------ Properties
    @property
    def occupancy_ratio(self) -> float:
        return self.current / self.capacity if self.capacity > 0 else 0.0

    @property
    def available_slots(self) -> int:
        return max(0, self.capacity - self.current)

    @property
    def status(self) -> LotStatus:
        r = self.occupancy_ratio
        if r >= 1.0:
            return LotStatus.OVERFLOW if self.current > self.capacity else LotStatus.FULL
        elif r >= self.alert_ratio:
            return LotStatus.ALMOST_FULL
        return LotStatus.AVAILABLE

    @property
    def revenue(self) -> float:
        return self._revenue

    # ------------------------------------------------------------------ Methods
    def vehicle_enter(self, vehicle_type: str = "car"):
        self.current  += 1
        self.total_in += 1
        self.peak      = max(self.peak, self.current)
        self._revenue += self.fee_per_vehicle

        self._log_event("ENTER", f"Xe {vehicle_type} vào bãi — còn {self.available_slots} chỗ", vehicle_type)

        if self.status in (LotStatus.ALMOST_FULL, LotStatus.FULL, LotStatus.OVERFLOW):
            self._log_alert()

    def vehicle_exit(self, vehicle_type: str = "car"):
        if self.current > 0:
            self.current   -= 1
            self.total_out += 1
        self._log_event("EXIT", f"Xe {vehicle_type} ra bãi — còn {self.available_slots} chỗ", vehicle_type)

    def _log_event(self, event_type: str, desc: str, vehicle_type: str = None):
        self.events.append(ParkingEvent(
            time=datetime.now().strftime("%H:%M:%S"),
            event_type=event_type,
            description=desc,
            vehicle_type=vehicle_type,
        ))
        # Chỉ giữ 200 sự kiện gần nhất
        if len(self.events) > 200:
            self.events = self.events[-200:]

    def _log_alert(self):
        status_msg = self.status.value
        self.events.append(ParkingEvent(
            time=datetime.now().strftime("%H:%M:%S"),
            event_type="ALERT",
            description=f"⚠ CẢNH BÁO: Bãi {status_msg} ({self.occupancy_ratio:.0%})",
        ))

    def sync_from_counter(self, total_in: int, total_out: int):
        """
        Đồng bộ dữ liệu từ LineCounter về.
        Gọi mỗi frame để giữ manager đúng với counter.
        """
        delta_in  = total_in  - self.total_in
        delta_out = total_out - self.total_out

        for _ in range(delta_in):
            self.vehicle_enter()

        for _ in range(delta_out):
            self.vehicle_exit()

    def get_stats(self) -> Dict:
        return {
            "current":          self.current,
            "capacity":         self.capacity,
            "available":        self.available_slots,
            "occupancy":        round(self.occupancy_ratio * 100, 1),
            "total_in":         self.total_in,
            "total_out":        self.total_out,
            "peak":             self.peak,
            "status":           self.status.value,
            "revenue_vnd":      int(self._revenue),
        }
