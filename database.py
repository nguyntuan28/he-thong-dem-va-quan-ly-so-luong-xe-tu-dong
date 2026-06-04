"""
SQLite Database Manager for Vehicle Detection System
Lưu trữ lịch sử xử lý video, thống kê, và thông tin vi phạm
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class DatabaseManager:
    """Quản lý SQLite database cho hệ thống phát hiện xe"""
    
    def __init__(self, db_path: str = 'vehicle_detection.db'):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
    
    def connect(self) -> bool:
        """Kết nối đến SQLite database"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Trả về rows như dict
            print(f"✓ Kết nối SQLite: {self.db_path}")
            return True
        except sqlite3.Error as e:
            print(f"✗ Lỗi kết nối SQLite: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Ngắt kết nối database"""
        try:
            if self.connection:
                self.connection.close()
                print("✓ Ngắt kết nối SQLite")
            return True
        except sqlite3.Error as e:
            print(f"✗ Lỗi ngắt kết nối: {e}")
            return False
    
    def create_database(self) -> bool:
        """SQLite tự động tạo database khi connect"""
        return True
    
    def reconnect_to_db(self) -> bool:
        """Với SQLite, disconnect rồi reconnect để tương thích với app.py"""
        return self.connect()
    
    def create_tables(self) -> bool:
        """Tạo các bảng database nếu chưa tồn tại"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Bảng jobs - Thông tin công việc
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    status TEXT DEFAULT 'queued',
                    progress INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    duration_seconds REAL,
                    file_size_mb REAL,
                    output_video_path TEXT,
                    confidence REAL,
                    iou REAL,
                    line_ratio REAL,
                    capacity INTEGER
                )
            ''')
            
            # Bảng job_stats - Thống kê xử lý
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE NOT NULL,
                    total_frames INTEGER,
                    fps REAL,
                    video_duration REAL,
                    total_vehicles_in INTEGER,
                    total_vehicles_out INTEGER,
                    peak_vehicles INTEGER,
                    flow_rate REAL,
                    traffic_density REAL,
                    congestion_level TEXT,
                    violations_severe INTEGER DEFAULT 0,
                    violations_moderate INTEGER DEFAULT 0,
                    violations_minor INTEGER DEFAULT 0,
                    violation_rate REAL,
                    vehicle_details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(job_id) REFERENCES jobs(job_id)
                )
            ''')
            
            # Bảng violations - Thông tin vi phạm
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    violation_id TEXT,
                    track_id INTEGER,
                    vehicle_type TEXT,
                    timestamp TEXT,
                    frame_number INTEGER,
                    severity TEXT,
                    image_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(job_id) REFERENCES jobs(job_id)
                )
            ''')
            
            self.connection.commit()
            print("✓ Tạo bảng SQLite thành công")
            return True
        except sqlite3.Error as e:
            print(f"✗ Lỗi tạo bảng: {e}")
            return False
    
    def save_job(self, job_data: Dict) -> bool:
        """Lưu thông tin job mới"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO jobs 
                (job_id, filename, status, progress, created_at, confidence, iou, line_ratio, capacity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_data.get('job_id'),
                job_data.get('filename'),
                job_data.get('status', 'queued'),
                job_data.get('progress', 0),
                job_data.get('created_at', datetime.now()),
                job_data.get('confidence'),
                job_data.get('iou'),
                job_data.get('line_ratio'),
                job_data.get('capacity')
            ))
            
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"✗ Lỗi lưu job: {e}")
            return False
    
    def update_job_completion(self, job_id: str, stats: Dict, output_path: str = None) -> bool:
        """Cập nhật job khi hoàn thành"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            now = datetime.now()
            
            # Cập nhật jobs table
            cursor.execute('''
                UPDATE jobs 
                SET status = ?, progress = ?, completed_at = ?, output_video_path = ?, duration_seconds = ?
                WHERE job_id = ?
            ''', ('completed', 100, now, output_path, stats.get('video_duration'), job_id))
            
            # Lưu stats vào job_stats table
            vehicle_details = stats.get('vehicle_details', {})
            cursor.execute('''
                INSERT OR REPLACE INTO job_stats 
                (job_id, total_frames, fps, video_duration, total_vehicles_in, total_vehicles_out,
                 peak_vehicles, flow_rate, traffic_density, congestion_level,
                 violations_severe, violations_moderate, violations_minor, violation_rate, vehicle_details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id,
                stats.get('total_frames'),
                stats.get('fps'),
                stats.get('video_duration'),
                stats.get('total_vehicles_in'),
                stats.get('total_vehicles_out'),
                stats.get('peak_vehicles'),
                stats.get('average_flow_rate'),
                stats.get('traffic_density'),
                stats.get('congestion_level'),
                len(stats.get('severe_violations', [])),
                len(stats.get('moderate_violations', [])),
                len(stats.get('minor_violations', [])),
                stats.get('violation_rate'),
                json.dumps(vehicle_details)
            ))
            
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"✗ Lỗi cập nhật hoàn thành: {e}")
            return False
    
    def save_job_error(self, job_id: str, error_message: str) -> bool:
        """Lưu thông tin lỗi job"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                'UPDATE jobs SET status = ?, progress = ?, completed_at = ? WHERE job_id = ?',
                ('error', 0, datetime.now(), job_id)
            )
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"✗ Lỗi lưu error: {e}")
            return False
    
    def save_violations(self, job_id: str, violations: List[Dict]) -> bool:
        """Lưu danh sách vi phạm"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            for violation in violations:
                cursor.execute('''
                    INSERT INTO violations 
                    (job_id, violation_id, track_id, vehicle_type, timestamp, frame_number, severity, image_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job_id,
                    violation.get('violation_id'),
                    violation.get('track_id'),
                    violation.get('vehicle_type'),
                    violation.get('timestamp'),
                    violation.get('frame_number'),
                    violation.get('severity'),
                    violation.get('image_path')
                ))
            
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"✗ Lỗi lưu violations: {e}")
            return False
    
    def get_job_history(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Lấy danh sách jobs"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT j.job_id, j.filename, j.status, j.created_at,
                       COALESCE(s.total_vehicles_in, 0) as total_vehicles_in,
                       COALESCE(s.violations_severe + s.violations_moderate + s.violations_minor, 0) as total_violations
                FROM jobs j
                LEFT JOIN job_stats s ON j.job_id = s.job_id
                ORDER BY j.created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"✗ Lỗi lấy history: {e}")
            return []
    
    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """Lấy chi tiết một job"""
        if not self.connection:
            return None
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT j.*, s.* 
                FROM jobs j
                LEFT JOIN job_stats s ON j.job_id = s.job_id
                WHERE j.job_id = ?
            ''', (job_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            print(f"✗ Lỗi lấy job details: {e}")
            return None
    
    def get_violations_by_job(self, job_id: str) -> List[Dict]:
        """Lấy danh sách vi phạm của một job"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                'SELECT * FROM violations WHERE job_id = ? ORDER BY frame_number DESC',
                (job_id,)
            )
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"✗ Lỗi lấy violations: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Lấy thống kê tổng hợp"""
        if not self.connection:
            return {}
        
        try:
            cursor = self.connection.cursor()
            
            # Tổng jobs
            cursor.execute('SELECT COUNT(*) as count FROM jobs')
            total_jobs = cursor.fetchone()[0]
            
            # Jobs hoàn thành
            cursor.execute("SELECT COUNT(*) as count FROM jobs WHERE status = 'completed'")
            completed_jobs = cursor.fetchone()[0]
            
            # Tổng vi phạm
            cursor.execute('''
                SELECT COALESCE(SUM(violations_severe + violations_moderate + violations_minor), 0) as total
                FROM job_stats
            ''')
            total_violations = cursor.fetchone()[0]
            
            # Tổng xe
            cursor.execute('SELECT COALESCE(SUM(total_vehicles_in), 0) as total FROM job_stats')
            total_vehicles = cursor.fetchone()[0]
            
            return {
                'total_jobs': total_jobs,
                'completed_jobs': completed_jobs,
                'total_violations': int(total_violations),
                'total_vehicles_processed': int(total_vehicles)
            }
        except sqlite3.Error as e:
            print(f"✗ Lỗi lấy statistics: {e}")
            return {}


# Khởi tạo instance global
db_manager = DatabaseManager('vehicle_detection.db')
