"""
app.py - Flask Web Server cho Vehicle Detection System
Hệ thống web để upload video, xử lý và nhận kết quả
"""

import os
import sys
import json
import cv2
import numpy as np
import logging
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path
import threading
import time
from datetime import datetime

# Thêm thư mục hiện tại vào path
sys.path.insert(0, os.path.dirname(__file__))

from detector import VehicleDetector
from counter import LineCounter
from manager import ParkingManager
from red_light_detector import RedLightDetector
from parking_detector import ParkingDetector, create_parking_detector
from database import db_manager
from chatbot import traffic_bot
from blockchain import blockchain_manager
from metamask_connector import metamask_connector

# Thêm import cho streaming
try:
    from flask import Response
except ImportError:
    pass

# ──────────────────────────────────────────────────────────
# Flask Configuration
# ──────────────────────────────────────────────────────────

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_url_path='/templates')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}

# Disable template caching for development
app.jinja_env.cache = None

# Configure logging
logger = logging.getLogger('app')
logging.basicConfig(level=logging.INFO)

# Tạo các thư mục nếu chưa có
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Global dictionary để theo dõi tiến độ xử lý
processing_jobs = {}

# Global dictionary để lưu frames đang xử lý (cho live stream)
processing_frames = {}
frame_lock = threading.Lock()

# Global settings cho violation detection line
global_settings = {
    'violation_line_ratio': 0.5,  # Vị trí đường phát hiện (0-1)
    'violation_line_visualize': True,  # Hiển thị đường trên video
    'violation_alert_enabled': True,  # Kích hoạt cảnh báo vi phạm
    'severity_threshold': 70,  # Ngưỡng mức độ vi phạm nguy hiểm (%)
    'min_violation_distance': 10,  # Khoảng cách tối thiểu (pixels)
    'min_detection_frames': 5  # Thời gian phát hiện tối thiểu (frames)
}


def allowed_file(filename):
    """Kiểm tra phần mở rộng file hợp lệ"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def process_video_worker(job_id, video_path, params):
    """
    Xử lý video trong thread riêng
    
    Args:
        job_id: ID của job xử lý
        video_path: Đường dẫn video input
        params: Dict chứa các tham số xử lý
    """
    try:
        # Log khởi đầu
        print(f"[{job_id}] ===== BẮT ĐẦU XỬ LÝ VIDEO =====")
        print(f"[{job_id}] Video path: {video_path}")
        print(f"[{job_id}] Params: {params}")
        
        processing_jobs[job_id]['status'] = 'processing'
        processing_jobs[job_id]['progress'] = 0
        
        # Kiểm tra file tồn tại
        if not os.path.exists(video_path):
            raise Exception(f"File video không tồn tại: {video_path}")
        
        file_size = os.path.getsize(video_path)
        print(f"[{job_id}] Kích thước file: {file_size / 1024 / 1024:.2f} MB")
        
        # Khởi tạo detector với confidence/IOU thấp hơn để nhận diện nhiều xe hơn
        print(f"[{job_id}] Đang tải model YOLO...")
        detector = VehicleDetector(
            model_path="yolov8n.pt",
            confidence=params.get('confidence', 0.25),  # Giảm từ 0.3 → 0.25 để nhận diện tốt hơn và đầy đủ hơn
            iou=params.get('iou', 0.30),               # Giảm từ 0.35 → 0.30 để nhận diện tốt hơn
            device="cpu"
        )
        print(f"[{job_id}] Model YOLO đã tải xong ✓")
        
        # Mở video
        print(f"[{job_id}] Đang mở video...")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Không thể mở video: {video_path}")
        
        # Lấy thông tin video
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        processing_jobs[job_id]['total_frames'] = total_frames
        
        # ──────────────────────────────────────────────────────────
        # Tối ưu hóa: Resize frame để tăng tốc độ xử lý
        # ──────────────────────────────────────────────────────────
        # Giữ tỉ lệ width=640 (hoặc nhỏ hơn nếu video nhỏ)
        resize_width = min(640, width)
        resize_height = int(resize_width * height / width)
        resize_scale = resize_width / width
        
        # Khởi tạo counter và manager với kích thước đã resize
        # Sử dụng line_ratio từ global_settings nếu có, nếu không dùng từ params
        line_ratio = params.get('line_ratio', global_settings.get('violation_line_ratio', 0.5))
        line_y = int(resize_height * line_ratio)  # Dùng resize_height
        counter = LineCounter(line_y=line_y, frame_w=resize_width, offset=6)
        manager = ParkingManager(
            capacity=params.get('capacity', 50),
            alert_ratio=0.85
        )
        
        # Khởi tạo red light detector
        red_light_detector = RedLightDetector(
            detection_line_y=line_y,
            frame_width=resize_width,
            frame_height=resize_height
        )
        
        # Thiết lập video writer (output video gốn dùng kích thước gốc)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        output_path = os.path.join(
            app.config['OUTPUT_FOLDER'],
            f"{job_id}_processed.mp4"
        )
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        detections_history = []
        last_stream_update = 0  # Để giới hạn cập nhật live stream
        
        # Xử lý từng frame
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # ──────────────────────────────────────────────────────────
            # Resize frame để tăng tốc độ xử lý (detection nhanh hơn)
            # ──────────────────────────────────────────────────────────
            frame_small = cv2.resize(frame, (resize_width, resize_height))
            
            # Phát hiện xe trên frame nhỏ (nhanh hơn)
            detections = detector.detect(frame_small)
            
            # Cập nhật bounding box trở lại kích thước gốc (để vẽ đúng trên output video)
            for det in detections:
                det.bbox = [int(coord / resize_scale) for coord in det.bbox]
                det.center = (int(det.center[0] / resize_scale), int(det.center[1] / resize_scale))
            detections_history.append(len(detections))
            
            # Đếm xe qua đường
            counter.update(detections)
            
            # Cập nhật trạng thái đèn giao thông (tự động)
            red_light_detector.update_light_status_auto(frame_count, fps)
            
            # Phát hiện vi phạm vượt đèn đỏ (dùng frame_small để nhanh hơn)
            violations = red_light_detector.detect_violation(detections, frame_count, fps, frame_small)
            
            # Cập nhật thống kê bãi đỗ
            current_vehicles = counter.current_inside()
            manager.current = current_vehicles
            manager.total_in = counter.total_in()
            manager.total_out = counter.total_out()
            manager.peak = max(manager.peak, current_vehicles)
            
            # Vẽ bounding box cho từng detection
            frame_annotated = frame.copy()
            for det in detections:
                x1, y1, x2, y2 = det.bbox
                color = (0, 255, 0)  # BGR: green
                cv2.rectangle(frame_annotated, (x1, y1), (x2, y2), color, 2)
                
                # Vẽ track ID
                cx, cy = det.center
                cv2.circle(frame_annotated, (cx, cy), 4, color, -1)
                cv2.putText(frame_annotated, f"ID:{det.track_id}", (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Vẽ đường đếm và thông tin lưu lượng
            frame_annotated = counter.draw(frame_annotated, detections)
            
            # Vẽ biểu tượng đèn giao thông
            frame_annotated = red_light_detector.draw_light_indicator(frame_annotated)
            
            # Vẽ thông tin vi phạm
            frame_annotated = red_light_detector.draw_violations(frame_annotated)
            
            # Vẽ đường phát hiện vi phạm nếu được bật
            if global_settings.get('violation_line_visualize', True):
                frame_annotated = red_light_detector.draw_detection_line(frame_annotated)
            
            # Ghi frame vào video output
            out.write(frame_annotated)
            
            # Lưu frame để phục vụ live stream - CHỈ update mỗi 500ms để giảm lag
            # (không update mỗi frame vì nó làm chậm xử lý)
            current_time = time.time()
            if current_time - last_stream_update >= 0.5:  # Cập nhật mỗi 500ms
                with frame_lock:
                    ret_encode, buffer = cv2.imencode('.jpg', frame_annotated, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    if ret_encode:
                        processing_frames[job_id] = {
                            'frame': buffer.tobytes(),
                            'progress': int((frame_count / total_frames) * 100),
                            'timestamp': datetime.now().isoformat()
                        }
                last_stream_update = current_time
            
            frame_count += 1
            progress = int((frame_count / total_frames) * 100)
            processing_jobs[job_id]['progress'] = progress
        
        # Đóng files
        cap.release()
        out.release()
        
        # Lưu kết quả thống kê
        counter_summary = counter.get_summary()
        red_light_summary = red_light_detector.get_violation_summary()
        
        # Tính flow rate metrics
        all_flow_rates = [f['flow_rate'] for f in counter.flow_history]
        average_flow = sum(all_flow_rates) / len(all_flow_rates) if all_flow_rates else 0
        peak_flow = max(all_flow_rates) if all_flow_rates else 0
        
        # Tính mật độ giao thông trung bình
        avg_density = (sum(detections_history) / len(detections_history) * 5) if detections_history else 0
        avg_density = min(100, avg_density)
        
        # Phân loại mức kẹt xe
        if peak_flow < 5 and counter_summary['total_in'] > 20:
            congestion = "VERY_HEAVY"
        elif average_flow < 10 or counter_summary['total_in'] > 15:
            congestion = "HEAVY"
        elif average_flow < 20 or counter_summary['total_in'] > 8:
            congestion = "MODERATE"
        elif average_flow < 30:
            congestion = "LIGHT"
        else:
            congestion = "FREE"
        
        # Lưu ảnh vi phạm vào thư mục
        violations_dir = os.path.join(app.config['OUTPUT_FOLDER'], f"{job_id}_violations")
        os.makedirs(violations_dir, exist_ok=True)
        
        violations_with_images = []
        for idx, violation in enumerate(red_light_detector.violations):
            violation_info = {
                'violation_id': idx,
                'timestamp': violation.timestamp,
                'track_id': violation.track_id,
                'vehicle_type': violation.vehicle_type,
                'frame_number': violation.frame_number,
                'severity': violation.violation_severity,
                'image_path': None
            }
            
            # Lưu ảnh vi phạm
            if violation.frame_image is not None:
                image_filename = f"violation_{idx:03d}_{violation.violation_severity.lower()}.jpg"
                image_path = os.path.join(violations_dir, image_filename)
                cv2.imwrite(image_path, violation.frame_image)
                violation_info['image_path'] = f"/api/violation/image/{job_id}/{idx}"
                violation.frame_path = image_path
            
            violations_with_images.append(violation_info)
        
        stats = {
            'total_frames': total_frames,
            'fps': fps,
            'video_duration': total_frames / fps if fps > 0 else 0,
            'total_vehicles_in': counter_summary.get('total_in', 0),
            'total_vehicles_out': counter_summary.get('total_out', 0),
            'current_vehicles': counter_summary.get('current_inside', 0),
            'capacity': manager.capacity,
            'vehicle_details': counter_summary.get('by_type', {}),
            # Flow monitoring metrics
            'average_flow_rate': average_flow,
            'peak_flow_rate': peak_flow,
            'traffic_density': avg_density,
            'congestion_level': congestion,
            'total_vehicles': counter_summary.get('total_in', 0),
            # Red light violation metrics
            'total_violations': red_light_summary['total_violations'],
            'severe_violations': red_light_summary['severe_violations'],
            'moderate_violations': red_light_summary['moderate_violations'],
            'minor_violations': red_light_summary['minor_violations'],
            'violation_rate': (red_light_summary['total_violations'] / counter_summary.get('total_in', 1)) * 100 if counter_summary.get('total_in', 0) > 0 else 0,
            'recent_violations': red_light_detector.get_recent_violations(10),
            'all_violations': violations_with_images  # Tất cả vi phạm với đường dẫn ảnh
        }
        
        stats_path = os.path.join(
            app.config['OUTPUT_FOLDER'],
            f"{job_id}_stats.json"
        )
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        processing_jobs[job_id]['status'] = 'completed'
        processing_jobs[job_id]['progress'] = 100
        processing_jobs[job_id]['output_video'] = output_path
        processing_jobs[job_id]['stats'] = stats
        print(f"[{job_id}] ===== XỬ LÝ HOÀN THÀNH =====")
        print(f"[{job_id}] Output video: {output_path}")
        
        # Lưu vào database
        try:
            db_manager.update_job_completion(job_id, stats, output_path)
            print(f"[{job_id}] [Database] Đã lưu lịch sử job")
        except Exception as db_error:
            print(f"[{job_id}] [Database Error] Không thể lưu lịch sử: {db_error}")
        
        # Xoá frames để tiết kiệm RAM
        with frame_lock:
            if job_id in processing_frames:
                del processing_frames[job_id]
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        
        print(f"[{job_id}] ===== LỖI XỬ LÝ VIDEO =====")
        print(f"[{job_id}] Error: {error_msg}")
        print(f"[{job_id}] Traceback:\n{error_traceback}")
        
        processing_jobs[job_id]['status'] = 'error'
        processing_jobs[job_id]['error'] = error_msg
        processing_jobs[job_id]['progress'] = 0
        
        # Lưu lỗi vào database
        try:
            cursor = db_manager.connection.cursor()
            cursor.execute(
                "UPDATE jobs SET status='error', completed_at=%s WHERE job_id=%s",
                (datetime.now().isoformat(), job_id)
            )
            db_manager.connection.commit()
            cursor.close()
        except Exception as db_error:
            print(f"[Database Error] Không thể cập nhật lỗi: {db_error}")
        
        # Xoá frames khi lỗi
        with frame_lock:
            if job_id in processing_frames:
                del processing_frames[job_id]


# ──────────────────────────────────────────────────────────
# Webcam Streaming - Real-time Video Analysis
# ──────────────────────────────────────────────────────────

# Global variables for streaming
streaming_active = False
stream_camera_index = 0
stream_detector = None
stream_counter = None
stream_red_light_detector = None
stream_frame_buffer = None
stream_lock = threading.Lock()


def generate_stream_frames(camera_index=0, confidence=0.4, iou=0.45, line_ratio=0.5):
    """
    Tạo stream frame từ webcam với real-time detection
    
    Args:
        camera_index: Chỉ số camera (0 cho default)
        confidence: Confidence threshold cho detection
        iou: IOU threshold cho detection
        line_ratio: Vị trí đường đếm (0-1)
    """
    global streaming_active, stream_detector, stream_counter, stream_red_light_detector
    
    try:
        # Khởi tạo detector
        detector = VehicleDetector(
            model_path="yolov8n.pt",
            confidence=confidence,
            iou=iou,
            device="cpu"
        )
        
        # Mở camera
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            yield b'--frame\r\n'
            yield b'Content-Type: text/plain\r\n\r\n'
            yield b'Camera not found\r\n'
            return
        
        # Cài đặt resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            fps = 30
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Khởi tạo các thành phần
        line_y = int(height * line_ratio)
        counter = LineCounter(line_y=line_y, frame_w=width, offset=6)
        red_light_detector = RedLightDetector(
            detection_line_y=line_y,
            frame_width=width,
            frame_height=height
        )
        
        stream_detector = detector
        stream_counter = counter
        stream_red_light_detector = red_light_detector
        
        frame_count = 0
        
        while streaming_active:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Flip frame nếu cần (tùy vào camera)
            frame = cv2.flip(frame, 1)
            
            # Phát hiện xe
            detections = detector.detect(frame)
            
            # Đếm xe qua đường
            counter.update(detections)
            
            # Cập nhật trạng thái đèn giao thông
            red_light_detector.update_light_status_auto(frame_count, fps)
            
            # Phát hiện vi phạm vượt đèn đỏ
            violations = red_light_detector.detect_violation(detections, frame_count, fps)
            
            # Vẽ bounding box
            frame_annotated = frame.copy()
            for det in detections:
                x1, y1, x2, y2 = det.bbox
                color = (0, 255, 0)
                cv2.rectangle(frame_annotated, (x1, y1), (x2, y2), color, 2)
                
                cx, cy = det.center
                cv2.circle(frame_annotated, (cx, cy), 4, color, -1)
                cv2.putText(frame_annotated, f"ID:{det.track_id}", (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Vẽ đường đếm và thông tin
            frame_annotated = counter.draw(frame_annotated, detections)
            
            # Vẽ biểu tượng đèn
            frame_annotated = red_light_detector.draw_light_indicator(frame_annotated)
            
            # Vẽ thông tin vi phạm
            frame_annotated = red_light_detector.draw_violations(frame_annotated)
            
            # Vẽ đường phát hiện vi phạm nếu được bật
            if global_settings.get('violation_line_visualize', True):
                frame_annotated = red_light_detector.draw_detection_line(frame_annotated)
            
            # Thêm thông tin real-time
            cv2.putText(frame_annotated, f"FPS: {int(fps)}", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame_annotated, f"Vehicles: {len(detections)}", (20, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            flow_rate = counter.get_flow_rate()
            cv2.putText(frame_annotated, f"Flow: {flow_rate:.1f} veh/min", (20, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            congestion = counter.get_congestion_level(detections)
            cv2.putText(frame_annotated, f"Status: {congestion}", (20, 160),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Mã hóa frame thành JPEG
            ret, buffer = cv2.imencode('.jpg', frame_annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame = buffer.tobytes()
            
            # Gửi frame dưới dạng MJPEG
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n'
                   b'Content-Length: ' + str(len(frame)).encode() + b'\r\n\r\n' + frame + b'\r\n')
            
            frame_count += 1
        
        cap.release()
    
    except Exception as e:
        print(f"[Streaming Error] {e}")


# ──────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────

@app.route('/templates/<path:filename>')
def serve_template_files(filename):
    """Phục vụ các file từ thư mục templates"""
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'templates'), filename)

@app.route('/')
def index():
    """Trang chính - hiển thị giao diện upload"""
    import os
    
    print("DEBUG: index() function called!")
    
    # Serve template file directly to bypass Jinja2 caching
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'dashboard.html')
    print(f"DEBUG: template_path = {template_path}")
    
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"DEBUG: Read {len(content)} bytes from template file")
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    else:
        print(f"DEBUG: Template file not found!")
        return render_template('dashboard.html')


@app.route('/api/upload', methods=['POST'])
def upload_video():
    """Upload video và bắt đầu xử lý"""
    try:
        # Kiểm tra file có được gửi không
        if 'file' not in request.files:
            return jsonify({'error': 'Không có file được gửi'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Chưa chọn file'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Định dạng file không được hỗ trợ'}), 400
        
        # Lưu file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Kiểm tra file đã được lưu
        if not os.path.exists(file_path):
            return jsonify({'error': 'Không thể lưu file'}), 500
        
        file_size = os.path.getsize(file_path)
        print(f"[Upload] File saved: {filename} ({file_size / 1024 / 1024:.2f} MB)")
        
        # Lấy tham số xử lý
        confidence = float(request.form.get('confidence', 0.3))  # Giảm từ 0.4 → 0.3
        iou = float(request.form.get('iou', 0.35))              # Giảm từ 0.45 → 0.35
        capacity = int(request.form.get('capacity', 50))
        
        # Kiểm tra xem sử dụng global_settings hay không
        use_global_settings = request.form.get('use_global_settings', '0') == '1'
        if use_global_settings:
            # Sử dụng line_ratio từ global_settings
            line_ratio = global_settings.get('violation_line_ratio', 0.5)
            print(f"[Upload] Using global_settings - line_ratio: {line_ratio}")
        else:
            # Sử dụng line_ratio từ form
            line_ratio = float(request.form.get('line_ratio', 0.5))
            print(f"[Upload] Using form parameters - line_ratio: {line_ratio}")
        
        # Tạo job ID
        job_id = f"job_{timestamp}_{os.urandom(4).hex()}"
        
        # Lưu thông tin job
        processing_jobs[job_id] = {
            'status': 'queued',
            'filename': filename,
            'file_path': file_path,
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'params': {
                'confidence': confidence,
                'iou': iou,
                'capacity': capacity,
                'line_ratio': line_ratio
            }
        }
        
        print(f"[Upload] Job created: {job_id}")
        
        # Lưu job vào database
        try:
            db_manager.save_job({
                'job_id': job_id,
                'filename': filename,
                'status': 'queued',
                'created_at': processing_jobs[job_id]['created_at'],
                'confidence': confidence,
                'iou': iou,
                'line_ratio': line_ratio,
                'capacity': capacity
            })
            print(f"[Upload] [Database] Job {job_id} saved to database")
        except Exception as db_error:
            print(f"[Upload] [Database Error] Không thể tạo job: {db_error}")
        
        # Bắt đầu xử lý trong thread riêng
        params = {
            'confidence': confidence,
            'iou': iou,
            'capacity': capacity,
            'line_ratio': line_ratio
        }
        
        print(f"[Upload] Starting processing thread for {job_id}...")
        thread = threading.Thread(
            target=process_video_worker,
            args=(job_id, file_path, params),
            daemon=True
        )
        thread.start()
        print(f"[Upload] Processing thread started for {job_id}")
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Bắt đầu xử lý video'
        })
    
    except Exception as e:
        import traceback
        print(f"[Upload] Error: {str(e)}")
        print(f"[Upload] Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Lấy trạng thái xử lý của một job"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job không tìm thấy'}), 404
    
    job = processing_jobs[job_id]
    response = {
        'job_id': job_id,
        'status': job['status'],
        'progress': job['progress'],
        'filename': job.get('filename', '')
    }
    
    if job['status'] == 'completed':
        response['stats'] = job.get('stats', {})
    
    if job['status'] == 'error':
        response['error'] = job.get('error', 'Unknown error')
    
    return jsonify(response)


@app.route('/api/download/<job_id>')
def download_video(job_id):
    """Download video đã xử lý"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job không tìm thấy'}), 404
    
    job = processing_jobs[job_id]
    if job['status'] != 'completed':
        return jsonify({'error': 'Video chưa xử lý xong'}), 400
    
    output_path = job.get('output_video')
    if not output_path or not os.path.exists(output_path):
        return jsonify({'error': 'File không tìm thấy'}), 404
    
    return send_file(
        output_path,
        as_attachment=True,
        download_name=f"result_{job_id}.mp4"
    )


@app.route('/api/results/<job_id>')
def get_results(job_id):
    """Lấy kết quả thống kê của một job"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job không tìm thấy'}), 404
    
    job = processing_jobs[job_id]
    if job['status'] != 'completed':
        return jsonify({'error': 'Job chưa hoàn thành'}), 400
    
    return jsonify(job.get('stats', {}))


@app.route('/api/jobs')
def list_jobs():
    """Lấy danh sách tất cả jobs"""
    jobs_list = []
    for job_id, job in processing_jobs.items():
        jobs_list.append({
            'job_id': job_id,
            'filename': job.get('filename', ''),
            'status': job['status'],
            'progress': job['progress'],
            'created_at': job.get('created_at', '')
        })
    
    return jsonify({'jobs': sorted(jobs_list, key=lambda x: x['created_at'], reverse=True)})


# ──────────────────────────────────────────────────────────
# Streaming Routes - Real-time Video Analysis
# ──────────────────────────────────────────────────────────

@app.route('/api/stream/start', methods=['POST'])
def start_stream():
    """Bắt đầu stream từ webcam"""
    global streaming_active
    
    try:
        data = request.json or {}
        camera_index = int(data.get('camera', 0))
        confidence = float(data.get('confidence', 0.4))
        iou = float(data.get('iou', 0.45))
        # Sử dụng global_settings nếu không được cung cấp trong request
        line_ratio = float(data.get('line_ratio', global_settings.get('violation_line_ratio', 0.5)))
        
        streaming_active = True
        
        return jsonify({
            'success': True,
            'message': 'Bắt đầu stream từ webcam'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stream/stop', methods=['POST'])
def stop_stream():
    """Dừng stream"""
    global streaming_active
    streaming_active = False
    
    return jsonify({
        'success': True,
        'message': 'Dừng stream'
    })


@app.route('/api/stream/video_feed')
def video_feed():
    """Stream video từ webcam"""
    global streaming_active
    
    confidence = float(request.args.get('confidence', 0.4))
    iou = float(request.args.get('iou', 0.45))
    camera = int(request.args.get('camera', 0))
    # Sử dụng global_settings nếu không được cung cấp trong request
    line_ratio = float(request.args.get('line_ratio', global_settings.get('violation_line_ratio', 0.5)))
    
    streaming_active = True
    
    return Response(
        generate_stream_frames(camera, confidence, iou, line_ratio),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/api/stream/stats')
def get_stream_stats():
    """Lấy thống kê hiện tại từ stream"""
    global stream_counter, stream_red_light_detector
    
    try:
        if not stream_counter:
            return jsonify({'error': 'Stream không hoạt động'}), 400
        
        stats = {
            'flow_rate': stream_counter.get_flow_rate() if stream_counter else 0,
            'total_vehicles_in': stream_counter.total_in() if stream_counter else 0,
            'total_vehicles_out': stream_counter.total_out() if stream_counter else 0,
            'violations': stream_red_light_detector.get_violation_summary() if stream_red_light_detector else {}
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ──────────────────────────────────────────────────────────
# Processing Video Live Stream Routes - Real-time Video Analysis
# ──────────────────────────────────────────────────────────

@app.route('/api/stream/processing/<job_id>')
def stream_processing_video(job_id):
    """Stream video đang được xử lý dưới dạng MJPEG"""
    print(f"[Stream] Client requested stream for job {job_id}")
    
    def generate_processing_frames():
        frame_count = 0
        while True:
            # Kiểm tra xem job có tồn tại không
            if job_id not in processing_jobs:
                print(f"[Stream] Job {job_id} not found")
                yield b'--frame\r\n'
                yield b'Content-Type: text/plain\r\n\r\n'
                yield b'Job not found\r\n'
                break
            
            job = processing_jobs[job_id]
            
            # Nếu job hoàn thành hoặc lỗi, dừng stream
            if job['status'] in ['completed', 'error']:
                print(f"[Stream] Job {job_id} finished with status: {job['status']}")
                yield b'--frame\r\n'
                yield b'Content-Type: text/plain\r\n\r\n'
                yield b'Processing finished\r\n'
                break
            
            # Lấy frame hiện tại
            with frame_lock:
                if job_id in processing_frames:
                    frame_data = processing_frames[job_id]['frame']
                    frame = frame_data
                else:
                    # Nếu chưa có frame, gửi placeholder
                    import time
                    time.sleep(0.1)
                    frame_count += 1
                    if frame_count % 50 == 0:  # Log mỗi 50 lần để tránh spam
                        print(f"[Stream] Waiting for frames for job {job_id}...")
                    continue
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n'
                   b'Content-Length: ' + str(len(frame)).encode() + b'\r\n\r\n' + frame + b'\r\n')
            
            import time
            time.sleep(0.03)  # ~30 FPS
    
    return Response(
        generate_processing_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/api/processing/stats/<job_id>')
def get_processing_stats(job_id):
    """Lấy thống kê live trong quá trình xử lý video"""
    if job_id not in processing_jobs:
        print(f"[API] Job not found: {job_id}")
        return jsonify({'error': 'Job không tìm thấy'}), 404
    
    job = processing_jobs[job_id]
    
    # Lấy thông tin frame hiện tại nếu đang xử lý
    frame_info = None
    with frame_lock:
        if job_id in processing_frames:
            frame_info = {
                'progress': processing_frames[job_id]['progress'],
                'timestamp': processing_frames[job_id]['timestamp']
            }
    
    response = {
        'job_id': job_id,
        'status': job['status'],
        'progress': job['progress'],
        'filename': job.get('filename', ''),
        'frame_info': frame_info
    }
    
    if job['status'] == 'completed' or job['status'] == 'error':
        response['stats'] = job.get('stats', {})
        if job['status'] == 'error':
            response['error'] = job.get('error', 'Unknown error')
            print(f"[API] Job {job_id} error: {response['error']}")
    
    return jsonify(response)


# ──────────────────────────────────────────────────────────
# Violation Image Routes
# ──────────────────────────────────────────────────────────

@app.route('/api/violation/image/<job_id>/<int:violation_id>')
def get_violation_image(job_id, violation_id):
    """Lấy ảnh của một lần vi phạm"""
    try:
        violations_dir = os.path.join(app.config['OUTPUT_FOLDER'], f"{job_id}_violations")
        
        if not os.path.exists(violations_dir):
            return jsonify({'error': 'Violation folder not found'}), 404
        
        # Tìm ảnh vi phạm
        for filename in os.listdir(violations_dir):
            if filename.startswith(f"violation_{violation_id:03d}_"):
                image_path = os.path.join(violations_dir, filename)
                return send_file(
                    image_path,
                    mimetype='image/jpeg',
                    as_attachment=False
                )
        
        return jsonify({'error': 'Violation image not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/violations/<job_id>')
def get_all_violations(job_id):
    """Lấy danh sách tất cả vi phạm của một job"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job không tìm thấy'}), 404
    
    job = processing_jobs[job_id]
    
    if job['status'] != 'completed':
        return jsonify({'error': 'Job chưa hoàn thành'}), 400
    
    stats = job.get('stats', {})
    all_violations = stats.get('all_violations', [])
    
    return jsonify({'violations': all_violations})


# ──────────────────────────────────────────────────────────
# Settings API Endpoints
# ──────────────────────────────────────────────────────────

@app.route('/api/settings/violation-line', methods=['POST'])
def update_violation_line_settings():
    """Cập nhật cấu hình đường phát hiện vi phạm"""
    global global_settings
    
    try:
        data = request.get_json()
        
        if 'line_ratio' in data:
            ratio = float(data['line_ratio'])
            if 0.1 <= ratio <= 0.9:
                global_settings['violation_line_ratio'] = ratio
            else:
                return jsonify({'success': False, 'error': 'Tỉ lệ phải từ 0.1 đến 0.9'}), 400
        
        if 'visualize' in data:
            global_settings['violation_line_visualize'] = bool(data['visualize'])
        
        if 'alert_enabled' in data:
            global_settings['violation_alert_enabled'] = bool(data['alert_enabled'])
        
        return jsonify({'success': True, 'settings': global_settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/settings/detection', methods=['POST'])
def update_detection_settings():
    """Cập nhật cấu hình tham số phát hiện"""
    global global_settings
    
    try:
        data = request.get_json()
        
        if 'severity_threshold' in data:
            global_settings['severity_threshold'] = int(data['severity_threshold'])
        
        if 'min_violation_distance' in data:
            global_settings['min_violation_distance'] = int(data['min_violation_distance'])
        
        if 'min_detection_frames' in data:
            global_settings['min_detection_frames'] = int(data['min_detection_frames'])
        
        return jsonify({'success': True, 'settings': global_settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/settings', methods=['GET'])
def get_all_settings():
    """Lấy tất cả cấu hình hiện tại"""
    return jsonify({'settings': global_settings})


# ──────────────────────────────────────────────────────────
# Database History API Endpoints
# ──────────────────────────────────────────────────────────

@app.route('/api/history', methods=['GET'])
def get_history():
    """Lấy lịch sử xử lý video"""
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        history = db_manager.get_job_history(limit, offset)
        
        return jsonify({
            'success': True,
            'history': history,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/history/<job_id>', methods=['GET'])
def get_history_detail(job_id):
    """Lấy chi tiết lịch sử của một job"""
    try:
        job_details = db_manager.get_job_details(job_id)
        violations = db_manager.get_violations_by_job(job_id)
        
        if not job_details:
            return jsonify({'error': 'Job không tìm thấy'}), 404
        
        return jsonify({
            'success': True,
            'job': job_details,
            'violations': violations
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Lấy thống kê tổng hợp từ database"""
    try:
        stats = db_manager.get_statistics()
        return jsonify({'success': True, 'statistics': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/database/init', methods=['POST'])
def init_database():
    """Khởi tạo database (chỉ gọi một lần)"""
    try:
        if not db_manager.connection or not db_manager.connection.is_connected():
            if not db_manager.connect():
                return jsonify({'success': False, 'error': 'Không thể kết nối MySQL'}), 500
        
        if not db_manager.create_database():
            return jsonify({'success': False, 'error': 'Không thể tạo database'}), 500
        
        if not db_manager.reconnect_to_db():
            return jsonify({'success': False, 'error': 'Không thể kết nối tới database'}), 500
        
        if not db_manager.create_tables():
            return jsonify({'success': False, 'error': 'Không thể tạo bảng'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Database đã được khởi tạo thành công'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Xử lý lỗi file quá lớn"""
    return jsonify({'error': 'File quá lớn (tối đa 500MB)'}), 413


# ──────────────────────────────────────────────────────────
# CHATBOT API ENDPOINTS
# ──────────────────────────────────────────────────────────

@app.route('/api/chatbot/message', methods=['POST'])
def chatbot_message():
    """Gửi tin nhắn tới chatbot"""
    try:
        if not traffic_bot:
            return jsonify({'error': 'Chatbot chưa được khởi tạo'}), 500
        
        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Tin nhắn không được để trống'}), 400
        
        # Chuẩn bị ngữ cảnh từ database
        context = {}
        try:
            stats = db_manager.get_statistics()
            if stats:
                context['total_vehicles'] = stats.get('total_vehicles', 0)
                context['total_violations'] = stats.get('total_violations', 0)
                context['job_count'] = stats.get('job_count', 0)
        except:
            pass
        
        # Lấy phản hồi từ chatbot
        response = traffic_bot.chat(user_message, context)
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chatbot/history', methods=['GET'])
def chatbot_history():
    """Lấy lịch sử trò chuyện"""
    try:
        if not traffic_bot:
            return jsonify({'error': 'Chatbot chưa được khởi tạo'}), 500
        
        limit = request.args.get('limit', 20, type=int)
        history = traffic_bot.get_history(limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chatbot/clear', methods=['POST'])
def chatbot_clear():
    """Xóa lịch sử trò chuyện"""
    try:
        if not traffic_bot:
            return jsonify({'error': 'Chatbot chưa được khởi tạo'}), 500
        
        traffic_bot.clear_history()
        
        return jsonify({
            'success': True,
            'message': 'Lịch sử đã được xóa'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chatbot/status', methods=['GET'])
def chatbot_status():
    """Lấy trạng thái chatbot"""
    try:
        if not traffic_bot:
            return jsonify({
                'success': False,
                'status': 'Chatbot chưa được khởi tạo',
                'using_openai': False
            }), 500
        
        status = traffic_bot.get_status()
        
        return jsonify({
            'success': True,
            **status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ──────────────────────────────────────────────────────────
# BLOCKCHAIN & METAMASK API ENDPOINTS
# ──────────────────────────────────────────────────────────

@app.route('/api/blockchain/status', methods=['GET'])
def blockchain_status():
    """Lấy trạng thái blockchain"""
    try:
        status = blockchain_manager.get_network_status()
        return jsonify({'success': True, 'blockchain': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/blockchain/connect', methods=['POST'])
def blockchain_connect():
    """Kết nối blockchain với private key hoặc MetaMask"""
    try:
        data = request.json or {}
        private_key = data.get('private_key', '').strip()
        contract_address = data.get('contract_address', '').strip()
        network = data.get('network', 'sepolia')
        
        if not private_key:
            return jsonify({'success': False, 'error': 'Private key không được để trống'}), 400
        
        if not contract_address:
            return jsonify({'success': False, 'error': 'Contract address không được để trống'}), 400
        
        # Khởi tạo lại BlockchainManager với network chọn
        global blockchain_manager
        from blockchain import BlockchainManager
        blockchain_manager = BlockchainManager(network=network)
        
        # Kết nối ví
        if blockchain_manager.connect_wallet(private_key, contract_address):
            return jsonify({
                'success': True,
                'message': f'Kết nối blockchain {network} thành công',
                'account': blockchain_manager.account.address if blockchain_manager.account else None,
                'balance': blockchain_manager.get_account_balance()
            })
        else:
            return jsonify({'success': False, 'error': 'Kết nối blockchain thất bại'}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/blockchain/record-violation', methods=['POST'])
def record_violation_blockchain():
    """Ghi vi phạm lên blockchain"""
    try:
        data = request.json or {}
        vehicle_id = data.get('vehicle_id', '').strip()
        violation_type = data.get('violation_type', 'red_light')
        severity = data.get('severity', 'moderate')
        location = data.get('location', 'Unknown')
        image_hash = data.get('image_hash', '')
        
        if not vehicle_id:
            return jsonify({'success': False, 'error': 'Vehicle ID không được để trống'}), 400
        
        # Ghi vi phạm lên blockchain
        result = blockchain_manager.record_violation(
            vehicle_id=vehicle_id,
            violation_type=violation_type,
            severity=severity,
            location=location,
            image_hash=image_hash
        )
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Vi phạm đã được ghi lên blockchain',
                'transaction': result
            })
        else:
            return jsonify({'success': False, 'error': 'Ghi vi phạm thất bại'}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/blockchain/update-violation', methods=['POST'])
def update_violation_blockchain():
    """Cập nhật vi phạm trên blockchain"""
    try:
        data = request.json or {}
        tx_hash = data.get('tx_hash', '')
        vehicle_id = data.get('vehicle_id', '').strip()
        violation_type = data.get('violation_type', 'red_light')
        severity = data.get('severity', 'moderate')
        location = data.get('location', 'Unknown')
        image_hash = data.get('image_hash', '')
        
        if not vehicle_id or not tx_hash:
            return jsonify({'success': False, 'error': 'Vehicle ID và TX Hash không được để trống'}), 400
        
        # Cập nhật vi phạm trong database (Mock implementation - cần blockchain thực tế để update trên chain)
        result = blockchain_manager.record_violation(
            vehicle_id=vehicle_id,
            violation_type=violation_type,
            severity=severity,
            location=location,
            image_hash=image_hash
        )
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Vi phạm đã được cập nhật',
                'transaction': result
            })
        else:
            return jsonify({'success': False, 'error': 'Cập nhật vi phạm thất bại'}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/blockchain/violation/<violation_hash>', methods=['GET'])
def get_blockchain_violation(violation_hash):
    """Lấy thông tin vi phạm từ blockchain"""
    try:
        violation = blockchain_manager.get_violation(violation_hash)
        
        if violation:
            return jsonify({'success': True, 'violation': violation})
        else:
            return jsonify({'success': False, 'error': 'Vi phạm không tìm thấy'}), 404
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/blockchain/violations/<vehicle_id>', methods=['GET'])
def get_vehicle_blockchain_violations(vehicle_id):
    """Lấy tất cả vi phạm của một xe từ blockchain"""
    try:
        violations = blockchain_manager.get_vehicle_violations(vehicle_id)
        
        if violations is not None:
            return jsonify({
                'success': True,
                'vehicle_id': vehicle_id,
                'violations': violations,
                'total': len(violations)
            })
        else:
            return jsonify({'success': False, 'error': 'Không thể lấy danh sách vi phạm'}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/blockchain/account-balance', methods=['GET'])
def get_blockchain_balance():
    """Lấy số dư tài khoản (ETH)"""
    try:
        balance = blockchain_manager.get_account_balance()
        
        if balance is not None:
            return jsonify({
                'success': True,
                'balance_eth': balance,
                'account': blockchain_manager.account.address if blockchain_manager.account else None
            })
        else:
            return jsonify({'success': False, 'error': 'Không thể lấy số dư'}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/blockchain/sync-violations', methods=['POST'])
def sync_blockchain_violations():
    """Đồng bộ các vi phạm chưa ghi blockchain"""
    try:
        synced = blockchain_manager.sync_pending_violations()
        
        return jsonify({
            'success': True,
            'message': f'Đã đồng bộ {synced} vi phạm lên blockchain',
            'synced_count': synced,
            'pending_count': len(blockchain_manager.violations_local)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metamask/connect', methods=['POST'])
def metamask_connect():
    """Xử lý kết nối MetaMask từ JavaScript"""
    try:
        data = request.json or {}
        account = data.get('account', '').strip()
        network_id = data.get('network_id', '11155111')
        
        result = metamask_connector.on_account_connected(account, network_id)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metamask/disconnect', methods=['POST'])
def metamask_disconnect():
    """Xử lý ngắt kết nối MetaMask"""
    try:
        result = metamask_connector.on_account_disconnected()
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metamask/network-changed', methods=['POST'])
def metamask_network_changed():
    """Xử lý đổi mạng trong MetaMask"""
    try:
        data = request.json or {}
        network_id = data.get('network_id', '')
        
        result = metamask_connector.on_network_changed(network_id)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metamask/status', methods=['GET'])
def metamask_status():
    """Lấy trạng thái kết nối MetaMask"""
    try:
        status = metamask_connector.get_connection_status()
        return jsonify({'success': True, 'metamask': status})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ──────────────────────────────────────────────────────────
# PARKING LOT DETECTION ROUTES
# ──────────────────────────────────────────────────────────

# Store parking detector per job
parking_detectors = {}
parking_jobs = {}


@app.route('/api/parking/upload', methods=['POST'])
def parking_lot_upload():
    """Upload video để phát hiện chỗ đỗ xe"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
        
        # Save uploaded file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get parameters
        confidence = float(request.form.get('confidence', 0.25))
        method = request.form.get('method', 'grid')
        cols = int(request.form.get('parkingCols', 5))
        rows = int(request.form.get('parkingRows', 3))
        
        # Create job for parking analysis
        parking_job_id = f"parking_{timestamp}_{np.random.randint(10000, 99999)}"
        parking_jobs[parking_job_id] = {
            'status': 'PROCESSING',
            'filepath': filepath,
            'filename': filename,
            'created_at': datetime.now().isoformat(),
            'progress': 0,
            'method': method,
            'cols': cols,
            'rows': rows
        }
        
        # Create parking detector
        parking_detectors[parking_job_id] = create_parking_detector(
            confidence=confidence
        )
        
        # Start processing in background
        thread = threading.Thread(
            target=process_parking_video,
            args=(parking_job_id, filepath, method, cols, rows)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'parking_job_id': parking_job_id,
            'message': 'Video đang được xử lý'
        })
    
    except Exception as e:
        logger.error(f"❌ Parking upload error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/parking/configure-slots', methods=['POST'])
def configure_parking_slots():
    """Configure parking slots (grid-based)"""
    try:
        data = request.json
        parking_job_id = data.get('parking_job_id')
        
        if parking_job_id not in parking_detectors:
            return jsonify({'success': False, 'error': 'Invalid job ID'}), 400
        
        detector = parking_detectors[parking_job_id]
        
        # Get grid parameters
        cols = data.get('cols', 5)
        rows = data.get('rows', 3)
        
        # Get video dimensions
        video_file = parking_jobs[parking_job_id]['filepath']
        cap = cv2.VideoCapture(video_file)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        # Create grid slots
        slots = detector.create_grid_slots(width, height, cols, rows)
        
        return jsonify({
            'success': True,
            'total_slots': len(slots),
            'slots': [
                {
                    'slot_id': s.slot_id,
                    'x': s.x,
                    'y': s.y,
                    'width': s.width,
                    'height': s.height
                }
                for s in slots
            ]
        })
    
    except Exception as e:
        logger.error(f"❌ Configure slots error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/parking/auto-detect', methods=['POST'])
def auto_detect_parking_lines():
    """Auto-detect parking lines from video frame"""
    try:
        data = request.json
        parking_job_id = data.get('parking_job_id')
        
        if parking_job_id not in parking_detectors:
            return jsonify({'success': False, 'error': 'Invalid job ID'}), 400
        
        detector = parking_detectors[parking_job_id]
        video_file = parking_jobs[parking_job_id]['filepath']
        
        # Read first frame
        cap = cv2.VideoCapture(video_file)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return jsonify({'success': False, 'error': 'Cannot read video'}), 400
        
        # Auto-detect lines
        lines = detector.auto_detect_parking_lines(frame)
        
        return jsonify({
            'success': True,
            'detected_lines': len(lines),
            'message': f'✓ Phát hiện được {len(lines)} đường kẻ bãi đỗ xe'
        })
    
    except Exception as e:
        logger.error(f"❌ Auto-detect error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/parking/occupancy/<parking_job_id>')
def get_parking_occupancy(parking_job_id):
    """Get current parking occupancy status"""
    try:
        if parking_job_id not in parking_detectors:
            return jsonify({'success': False, 'error': 'Invalid job ID'}), 400
        
        job = parking_jobs.get(parking_job_id, {})
        
        # If still processing, return current state
        if job.get('status') == 'PROCESSING':
            return jsonify({
                'success': True,
                'data': {
                    'stats': {
                        'total_slots': 0,
                        'occupied_slots': 0,
                        'empty_slots': 0,
                        'occupancy_rate': '0%'
                    },
                    'occupancy_history': [],
                    'empty_slots': [],
                    'occupied_slots': []
                },
                'message': 'Still processing...'
            })
        
        # Get results from completed job
        if job.get('status') == 'COMPLETED' and 'results' in job:
            results = job['results']
            parking_details = results.get('parking_details', {})
            
            return jsonify({
                'success': True,
                'data': parking_details
            })
        
        return jsonify({'success': False, 'error': 'Job not found or still processing'}), 400
    
    except Exception as e:
        logger.error(f"❌ Get occupancy error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/parking/status/<parking_job_id>')
def get_parking_status(parking_job_id):
    """Get parking job processing status"""
    try:
        if parking_job_id not in parking_jobs:
            return jsonify({'success': False, 'error': 'Invalid job ID'}), 400
        
        job = parking_jobs[parking_job_id]
        
        return jsonify({
            'success': True,
            'status': job['status'],
            'progress': job.get('progress', 0),
            'filename': job['filename'],
            'created_at': job['created_at']
        })
    
    except Exception as e:
        logger.error(f"❌ Get parking status error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/parking/video/<parking_job_id>')
def get_parking_video(parking_job_id):
    """Download parking visualization video"""
    try:
        if parking_job_id not in parking_jobs:
            return jsonify({'success': False, 'error': 'Invalid job ID'}), 400
        
        job = parking_jobs[parking_job_id]
        
        if job.get('status') != 'COMPLETED':
            return jsonify({'success': False, 'error': 'Job not completed yet'}), 400
        
        results = job.get('results', {})
        video_path = results.get('video_output')
        
        if not video_path or not os.path.exists(video_path):
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        return send_file(
            video_path,
            mimetype='video/mp4',
            as_attachment=True,
            download_name=f"{parking_job_id}_visualization.mp4"
        )
    
    except Exception as e:
        logger.error(f"❌ Get parking video error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


def process_parking_video(parking_job_id: str, video_path: str, method: str = 'grid', cols: int = 5, rows: int = 3):
    """Process parking lot video in background"""
    try:
        logger.info(f"🅿️ Processing parking video: {parking_job_id}")
        logger.info(f"  - Method: {method}, Grid: {rows}x{cols}")
        
        detector = parking_detectors[parking_job_id]
        vehicle_detector = VehicleDetector(
            confidence=0.25,
            iou=0.30
        )
        
        cap = cv2.VideoCapture(video_path)
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        frame_count = 0
        occupancy_data = []
        
        # Read first frame to initialize detector
        ret, first_frame = cap.read()
        if not ret:
            raise ValueError("Cannot read video file")
        
        height, width = first_frame.shape[:2]
        
        # Create grid slots for parking detection
        detector.create_grid_slots(width, height, cols=cols, rows=rows)
        logger.info(f"✓ Created grid slots: {len(detector.parking_slots)} slots ({rows}x{cols})")
        
        # Setup video writer for visualization
        output_video_path = os.path.join(
            app.config['OUTPUT_FOLDER'],
            f"{parking_job_id}_visualization.mp4"
        )
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        
        # Process video frames
        frame_count = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to first frame
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Update progress
            progress = int((frame_count / total_frames) * 100) if total_frames > 0 else 0
            parking_jobs[parking_job_id]['progress'] = progress
            
            # Every 5 frames, run detection
            if frame_count % 5 == 0:
                # Detect vehicles
                detection_objects = vehicle_detector.detect(frame)
                logger.info(f"Frame {frame_count}: {len(detection_objects)} vehicles detected")
                
                # Convert Detection objects to dictionaries
                detections_dicts = []
                for det in detection_objects:
                    detections_dicts.append({
                        'x1': det.bbox[0],
                        'y1': det.bbox[1],
                        'x2': det.bbox[2],
                        'y2': det.bbox[3],
                        'class_id': det.class_id,
                        'confidence': det.confidence,
                        'track_id': det.track_id
                    })
                
                # Update parking occupancy based on vehicle detections
                detector.detect_occupancy(frame, detections_dicts)
                
                # Get occupancy stats and add to history
                timestamp = datetime.now().isoformat()
                stats = detector.get_occupancy_stats(timestamp)
                detector.occupancy_history.append(stats)
                
                occupancy_data.append({
                    'timestamp': timestamp,
                    'total_slots': stats.total_slots,
                    'occupied_slots': stats.occupied_slots,
                    'empty_slots': stats.empty_slots,
                    'occupancy_rate': stats.occupancy_rate
                })
            
            # Draw parking visualization on every frame
            vis_frame = detector.draw_parking_visualization(frame, show_labels=True)
            
            # Add occupancy stats text on the frame
            if occupancy_data:
                latest_stats = occupancy_data[-1]
                stats_text = f"Total: {latest_stats['total_slots']} | Empty: {latest_stats['empty_slots']} | Occupied: {latest_stats['occupied_slots']} | Rate: {latest_stats['occupancy_rate']:.1f}%"
                cv2.putText(
                    vis_frame,
                    stats_text,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )
            
            # Write frame to output video
            out.write(vis_frame)
        
        cap.release()
        out.release()
        
        # Store results
        parking_jobs[parking_job_id]['status'] = 'COMPLETED'
        parking_jobs[parking_job_id]['progress'] = 100
        parking_jobs[parking_job_id]['results'] = {
            'occupancy_data': occupancy_data,
            'parking_details': detector.get_parking_details(),
            'video_output': output_video_path,
            'vehicle_detector': vehicle_detector
        }
        
        logger.info(f"✓ Parking video processing completed: {parking_job_id}")
        logger.info(f"  - Total frames: {frame_count}")
        logger.info(f"  - Occupancy records: {len(occupancy_data)}")
        logger.info(f"  - Output video: {output_video_path}")
        
    except Exception as e:
        logger.error(f"❌ Parking video processing error: {str(e)}")
        parking_jobs[parking_job_id]['status'] = 'ERROR'
        parking_jobs[parking_job_id]['error'] = str(e)
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    print("🚀 Khởi động Vehicle Detection Web Server...")
    
    # Khởi tạo database
    print("📊 Khởi tạo Database...")
    try:
        if not db_manager.connect():
            print("⚠️  Cảnh báo: Không thể kết nối MySQL - lệnh /api/database/init sẽ khởi tạo")
        else:
            if db_manager.create_database():
                if db_manager.reconnect_to_db():
                    if db_manager.create_tables():
                        print("✓ Database đã sẵn sàng")
                    else:
                        print("⚠️  Cảnh báo: Không thể tạo bảng")
                else:
                    print("⚠️  Cảnh báo: Không thể kết nối tới database")
            else:
                print("⚠️  Cảnh báo: Không thể tạo database")
    except Exception as e:
        print(f"⚠️  Cảnh báo: Database error: {e}")
    
    print("📺 Mở trình duyệt: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, threaded=True)
