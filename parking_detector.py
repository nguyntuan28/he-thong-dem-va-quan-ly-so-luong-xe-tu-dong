"""
Parking Lot Detection Module
Detects empty parking spaces using YOLOv8 and line detection
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParkingSlot:
    """Represents a single parking slot"""
    slot_id: int
    x: int
    y: int
    width: int
    height: int
    occupied: bool = False
    track_id: Optional[int] = None
    confidence: float = 0.0


@dataclass
class ParkingStats:
    """Parking lot statistics"""
    total_slots: int
    occupied_slots: int
    empty_slots: int
    occupancy_rate: float
    timestamp: str


class ParkingDetector:
    """Main parking lot detector using YOLOv8 and line detection"""
    
    def __init__(self, confidence_threshold=0.3, occupancy_threshold=0.3):
        self.confidence_threshold = confidence_threshold
        self.occupancy_threshold = occupancy_threshold
        
        # Store detected slots
        self.parking_slots: List[ParkingSlot] = []
        
        # Track vehicle positions
        self.vehicle_tracks: Dict[int, deque] = {}
        
        # History for occupancy trends
        self.occupancy_history: List[ParkingStats] = []
        
        # Auto-detected lines
        self.parking_lines: List[Tuple] = []
        
        logger.info("🅿️ ParkingDetector initialized")
    
    def auto_detect_parking_lines(self, frame: np.ndarray) -> List[Tuple]:
        """
        Auto-detect parking lot lines using edge detection and Hough transform
        Returns: List of line coordinates [(x1, y1, x2, y2), ...]
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Canny edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Dilate to connect nearby edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Hough line detection
        lines = cv2.HoughLinesP(
            dilated,
            rho=1,
            theta=np.pi/180,
            threshold=30,
            minLineLength=50,
            maxLineGap=10
        )
        
        detected_lines = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                detected_lines.append((x1, y1, x2, y2))
        
        self.parking_lines = detected_lines
        logger.info(f"🅿️ Auto-detected {len(detected_lines)} parking lines")
        return detected_lines
    
    def create_grid_slots(self, frame_width: int, frame_height: int, 
                         cols: int = 5, rows: int = 3, 
                         margin: int = 20) -> List[ParkingSlot]:
        """
        Create grid-based parking slots
        Args:
            frame_width: Video frame width
            frame_height: Video frame height
            cols: Number of parking slots per row
            rows: Number of rows
            margin: Margin around each slot
        """
        self.parking_slots = []
        
        slot_width = (frame_width - 2 * margin) // cols
        slot_height = (frame_height - 2 * margin) // rows
        
        slot_id = 0
        for row in range(rows):
            for col in range(cols):
                x = margin + col * slot_width
                y = margin + row * slot_height
                
                slot = ParkingSlot(
                    slot_id=slot_id,
                    x=x,
                    y=y,
                    width=slot_width,
                    height=slot_height,
                    occupied=False
                )
                self.parking_slots.append(slot)
                slot_id += 1
        
        logger.info(f"🅿️ Created {len(self.parking_slots)} parking slots ({rows}x{cols})")
        return self.parking_slots
    
    def detect_occupancy(self, frame: np.ndarray, detections: List[Dict]) -> List[ParkingSlot]:
        """
        Detect which parking slots are occupied based on vehicle detections
        
        Args:
            frame: Current video frame
            detections: YOLOv8 detections [{"x1": ..., "y1": ..., "x2": ..., "y2": ..., "track_id": ...}, ...]
        """
        if not self.parking_slots:
            return []
        
        # Reset occupancy
        for slot in self.parking_slots:
            slot.occupied = False
            slot.track_id = None
            slot.confidence = 0.0
        
        # Check each detection against each slot
        for detection in detections:
            if detection.get('class_id', 999) in [2, 3, 5, 7]:  # car, truck, bus, motorcycle
                veh_x1 = detection['x1']
                veh_y1 = detection['y1']
                veh_x2 = detection['x2']
                veh_y2 = detection['y2']
                veh_conf = detection.get('confidence', 0)
                veh_track_id = detection.get('track_id', -1)
                
                veh_center_x = (veh_x1 + veh_x2) / 2
                veh_center_y = (veh_y1 + veh_y2) / 2
                
                # Check which slot contains this vehicle center
                for slot in self.parking_slots:
                    if (slot.x <= veh_center_x <= slot.x + slot.width and
                        slot.y <= veh_center_y <= slot.y + slot.height):
                        
                        # Calculate overlap percentage
                        overlap_area = max(0, min(veh_x2, slot.x + slot.width) - max(veh_x1, slot.x)) * \
                                      max(0, min(veh_y2, slot.y + slot.height) - max(veh_y1, slot.y))
                        slot_area = slot.width * slot.height
                        overlap_ratio = overlap_area / slot_area if slot_area > 0 else 0
                        
                        # Mark as occupied if overlap > threshold
                        if overlap_ratio > self.occupancy_threshold:
                            slot.occupied = True
                            slot.track_id = veh_track_id
                            slot.confidence = veh_conf
        
        return self.parking_slots
    
    def get_occupancy_stats(self, timestamp: str) -> ParkingStats:
        """Calculate parking occupancy statistics"""
        if not self.parking_slots:
            return ParkingStats(0, 0, 0, 0.0, timestamp)
        
        total = len(self.parking_slots)
        occupied = sum(1 for slot in self.parking_slots if slot.occupied)
        empty = total - occupied
        occupancy_rate = (occupied / total * 100) if total > 0 else 0
        
        stats = ParkingStats(
            total_slots=total,
            occupied_slots=occupied,
            empty_slots=empty,
            occupancy_rate=occupancy_rate,
            timestamp=timestamp
        )
        
        self.occupancy_history.append(stats)
        return stats
    
    def draw_parking_visualization(self, frame: np.ndarray, show_labels: bool = True) -> np.ndarray:
        """
        Draw parking slots and occupancy status on frame
        
        Green: Empty
        Red: Occupied
        """
        result = frame.copy()
        
        for slot in self.parking_slots:
            # Color based on occupancy
            if slot.occupied:
                color = (0, 0, 255)  # Red for occupied
                thickness = 3
            else:
                color = (0, 255, 0)  # Green for empty
                thickness = 2
            
            # Draw rectangle
            cv2.rectangle(
                result,
                (slot.x, slot.y),
                (slot.x + slot.width, slot.y + slot.height),
                color,
                thickness
            )
            
            # Draw slot ID and status
            if show_labels:
                status = "✓" if slot.occupied else "○"
                cv2.putText(
                    result,
                    f"{slot.slot_id}{status}",
                    (slot.x + 5, slot.y + 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    color,
                    1
                )
        
        return result
    
    def draw_detected_lines(self, frame: np.ndarray) -> np.ndarray:
        """Draw auto-detected parking lines on frame"""
        result = frame.copy()
        
        for x1, y1, x2, y2 in self.parking_lines:
            cv2.line(result, (x1, y1), (x2, y2), (255, 255, 0), 2)
        
        return result
    
    def get_empty_slots_heatmap(self, frame: np.ndarray) -> np.ndarray:
        """
        Generate heatmap showing empty parking spaces
        Brighter = more likely empty
        """
        heatmap = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.float32)
        
        for slot in self.parking_slots:
            intensity = 0 if slot.occupied else 255
            cv2.rectangle(
                heatmap,
                (slot.x, slot.y),
                (slot.x + slot.width, slot.y + slot.height),
                intensity,
                -1
            )
        
        # Apply Gaussian blur for smooth transitions
        heatmap = cv2.GaussianBlur(heatmap, (21, 21), 0)
        
        # Convert to color heatmap
        heatmap_color = cv2.applyColorMap(heatmap.astype(np.uint8), cv2.COLORMAP_JET)
        
        return heatmap_color
    
    def get_parking_details(self) -> Dict:
        """Get detailed parking information"""
        stats = self.get_occupancy_stats("")
        
        occupied_slots_info = [
            {
                'slot_id': slot.slot_id,
                'x': slot.x,
                'y': slot.y,
                'track_id': slot.track_id,
                'confidence': slot.confidence
            }
            for slot in self.parking_slots if slot.occupied
        ]
        
        empty_slots_info = [
            {
                'slot_id': slot.slot_id,
                'x': slot.x,
                'y': slot.y
            }
            for slot in self.parking_slots if not slot.occupied
        ]
        
        return {
            'stats': {
                'total_slots': stats.total_slots,
                'occupied_slots': stats.occupied_slots,
                'empty_slots': stats.empty_slots,
                'occupancy_rate': f"{stats.occupancy_rate:.1f}%"
            },
            'occupied_slots': occupied_slots_info,
            'empty_slots': empty_slots_info,
            'history': [
                {
                    'timestamp': h.timestamp,
                    'occupancy_rate': f"{h.occupancy_rate:.1f}%",
                    'occupied': h.occupied_slots,
                    'empty': h.empty_slots
                }
                for h in self.occupancy_history[-10:]  # Last 10 records
            ]
        }


def create_parking_detector(confidence=0.3) -> ParkingDetector:
    """Factory function to create parking detector"""
    return ParkingDetector(confidence_threshold=confidence)
