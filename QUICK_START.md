# 🚀 Hướng dẫn Chạy Hệ thống Traffic Flow Monitoring

## 📋 Yêu cầu

- **Python**: 3.8+
- **RAM**: 4GB+ khuyến nghị
- **Disk**: 2GB để lưu videos + models
- **Camera/Video**: Tuỳ chọn (có thể upload file)

---

## 🔧 Cài đặt Lần Đầu

### 1. Clone/Download project

```bash
cd c:\Users\nguyn\Downloads\files (1)
```

### 2. Tạo virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Sau đó bạn sẽ thấy: (venv) C:\Users\nguyn\Downloads\files (1)>
```

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Kiểm tra YOLOv8 model

```bash
# Nên có file yolov8n.pt trong thư mục project
# Nếu không có, sẽ tự download khi chạy lần đầu (~40MB)
```

---

## ▶️ Chạy Hệ thống

### Bước 1: Activate virtual environment

```bash
# Nếu chưa active
venv\Scripts\activate
```

### Bước 2: Chạy Flask server

```bash
python app.py
```

Output sẽ giống như:
```
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

### Bước 3: Mở web browser

```
http://localhost:5000
```

Hoặc: http://127.0.0.1:5000

---

## 🌐 Giao Diện Web

Sẽ có 4 tabs:

### Tab 1️⃣ "📤 UPLOAD"
- Chọn file video (mp4, avi, mov, mkv, flv, wmv)
- Adjust parameters (confidence, IOU, capacity, line_ratio)
- Click "🚀 UPLOAD & XỰ LÝ"
- Sẽ mở modal phân tích trực tiếp

### Tab 2️⃣ "📹 LIVE"
- Click "📷 Start Webcam" để bắt đầu stream từ webcam
- Xem live stats (flow rate, vehicles, violations)
- Click "⏹️ Stop Webcam" để dừng

### Tab 3️⃣ "✅ KẾT QUẢ"
- Xem các job đã xử lý
- Status badge (queued, processing, completed, error)
- Progress bar
- Download button cho video output
- Chi tiết button

### Tab 4️⃣ "📋 CHI TIẾT"
- Hiển thị từ khi nhấp "Chi tiết" ở Tab 3
- Traffic flow stats (8 cards)
- Violation stats (5 cards)
- **📸 Vi phạm gần đây** - Click để xem ảnh chi tiết ← MỚI!

---

## 🎥 Upload & Xử lý Video

### Supported Formats
- MP4, AVI, MOV, MKV, FLV, WMV

### Max Size
- 500MB (có thể thay đổi ở app.py: MAX_CONTENT_LENGTH)

### Cách Upload

1. Tab 1 "📤 UPLOAD"
2. Drag & drop hoặc click "Choose File"
3. Adjust parameters:
   - **Confidence** (0-1): Ngưỡng detection (0.5 = 50%)
   - **IOU** (0-1): Overlapping threshold (0.5 = 50%)
   - **Capacity** (10-500): Dùng để tính congestion
   - **Line Ratio** (0.1-0.9): Vị trí line giao thông
4. Click "🚀 UPLOAD & XỰ LÝ"
5. Modal mở, xem video trực tiếp + tiến độ

---

## 📊 Thứ bạn sẽ thấy

### 1. Live Processing Modal
- Video stream (MJPEG)
- Progress bar (%)
- Status (queued/processing/completed)
- Frame timestamp

### 2. Traffic Flow Stats
- **Luồng hiện tại**: xe/phút bây giờ
- **Luồng trung bình**: average qua 1 giờ
- **Luồng cao nhất**: peak qua 1 giờ
- **Mật độ giao thông**: %
- **Mức độ kẹt đường**: FREE/LIGHT/MODERATE/HEAVY/VERY_HEAVY
- **Tổng xe**: đếm được
- **Tổng violations**: vi phạm đèn đỏ
- **Xe dừng**: dừng ở line

### 3. Violation Stats
- **Tổng vi phạm**: tất cả
- **Vi phạm SEVERE**: mức độ cao
- **Vi phạm MODERATE**: mức độ trung bình
- **Vi phạm MINOR**: mức độ thấp
- **Xe vi phạm**: số lượng xe unique

### 4. Violation Images ← MỚI!
- Danh sách vi phạm gần đây
- Click để xem ảnh chi tiết
- Modal hiển thị:
  - Ảnh xe vi phạm (cropped)
  - Thông tin: vehicle type, severity, time, track ID, frame number

---

## 🔴 Red Light Violation Detection

### Cách hoạt động

1. **Traffic light simulation**
   - GREEN (10s) → YELLOW (3s) → RED (10s)
   - Chu kỳ 23 giây
   - Tự động chuyển

2. **Phát hiện violation**
   - Track từng xe qua frames
   - Tính tốc độ: pixels/frame
   - Nếu tốc độ > ngưỡng trong RED → violation
   - **SEVERE**: tốc độ > 15 px/frame
   - **MODERATE**: 8-15 px/frame
   - **MINOR**: < 8 px/frame

3. **Lưu ảnh chứng cứ**
   - Crop frame quanh bbox detection
   - JPEG 85% quality
   - Lưu vào `outputs/{job_id}_violations/violation_000_severe.jpg`

---

## 📂 Cấu Trúc Thư Mục

```
c:\Users\nguyn\Downloads\files (1)\
├── app.py                          (Flask app chính)
├── detector.py                     (YOLOv8 detection)
├── counter.py                      (Traffic flow counting)
├── red_light_detector.py           (Violation detection)
├── manager.py                      (Job management)
├── hud.py                          (Visualization)
├── requirements.txt                (Dependencies)
├── yolov8n.pt                      (Model - nếu có)
├── THAY_DOI.txt                    (Change log)
├── VIOLATION_IMAGE_VIEWER.md       (Docs for new feature)
├── venv/                           (Virtual environment)
│
├── uploads/                        (User uploaded videos)
│   ├── video1.mp4
│   └── video2.avi
│
├── outputs/                        (Processing results)
│   ├── job_20240515_143025_abc_processed.mp4
│   ├── job_20240515_143025_abc_stats.json
│   └── job_20240515_143025_abc_violations/
│       ├── violation_000_severe.jpg
│       ├── violation_001_moderate.jpg
│       └── violation_002_minor.jpg
│
└── templates/
    └── dashboard.html              (Web interface)
```

---

## 🐛 Troubleshooting

### ❌ "ModuleNotFoundError: No module named 'flask'"
**Giải pháp**: Cài dependencies
```bash
pip install -r requirements.txt
```

### ❌ "Could not connect to localhost:5000"
**Giải pháp**: Kiểm tra Flask đã start
```bash
# Nên thấy: "Running on http://127.0.0.1:5000"
# Nếu không, check terminal for errors
```

### ❌ "Permission denied" khi upload
**Giải pháp**: Kiểm tra quyền folder
```bash
# Ensure uploads/ và outputs/ folders exist
mkdir uploads outputs
```

### ❌ "CUDA out of memory"
**Giải pháp**: Dùng CPU (mặc định đã là yolov8n-nano)
- Hoặc giảm video resolution trước khi upload

### ❌ Video processing rất chậm
**Giải pháp**:
- Giảm video resolution (upload 720p instead 1080p)
- Giảm FPS (convert to 15 fps if possible)
- Hoặc chờ, processing là background task

### ❌ Webcam không hoạt động
**Giải pháp**:
- Kiểm tra camera connected
- Kiểm tra permissions (Windows may ask)
- Test: `python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"`

### ❌ Ảnh vi phạm không hiển thị
**Giải pháp**:
- Check browser console (F12)
- Verify `/api/violations/<job_id>` trả về image_path
- Kiểm tra files trong `outputs/<job_id>_violations/`

---

## ⚡ Performance Tips

1. **Máy mạnh?** → Tăng confidence để detection chính xác hơn
2. **Máy yếu?** → Giảm confidence, giảm video resolution
3. **Video dài?** → Processing chạy background, có thể đóng browser
4. **Quá nhiều frames?** → Thay đổi DETECTION_EVERY_N_FRAMES ở app.py

---

## 🚀 Advanced Usage

### 1. Thay đổi Traffic Light Cycle
Edit `red_light_detector.py`:
```python
GREEN_DURATION = 10   # seconds
YELLOW_DURATION = 3
RED_DURATION = 10
```

### 2. Thay đổi Violation Severity Thresholds
Edit `red_light_detector.py`:
```python
SEVERE_THRESHOLD = 15  # px/frame
MODERATE_THRESHOLD = 8
```

### 3. Thay đổi Max Upload Size
Edit `app.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
```

### 4. Export Violations as CSV
```python
# Custom script to read outputs/{job_id}_stats.json
import json
stats = json.load(open(f"outputs/{job_id}_stats.json"))
for v in stats['all_violations']:
    print(f"{v['timestamp']},{v['vehicle_type']},{v['severity']}")
```

---

## 📝 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/upload` | Upload video |
| GET | `/api/status/<job_id>` | Job status |
| GET | `/api/download/<job_id>` | Download video |
| GET | `/api/results/<job_id>` | Stats |
| GET | `/api/jobs` | All jobs |
| POST | `/api/stream/start` | Start webcam |
| POST | `/api/stream/stop` | Stop webcam |
| GET | `/api/stream/video_feed` | MJPEG webcam |
| GET | `/api/stream/stats` | Webcam stats |
| GET | `/api/stream/processing/<job_id>` | Processing MJPEG |
| GET | `/api/processing/stats/<job_id>` | Processing stats |
| GET | `/api/violation/image/<job_id>/<id>` | Violation image ← MỚI! |
| GET | `/api/violations/<job_id>` | All violations ← MỚI! |

---

## ✅ Checklist Trước Khi Chạy

- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] uploads/ folder exists
- [ ] outputs/ folder exists
- [ ] yolov8n.pt exists (or will download auto)
- [ ] Port 5000 is not in use
- [ ] Flask starts without errors

---

## 🎉 Ready to Go!

Nếu tất cả bước trên OK:

```bash
python app.py
```

Đợi 2-3 giây, sau đó:

```
http://localhost:5000
```

Enjoy! 🚀

---

**Version**: 2.2 with Violation Image Viewer  
**Last Updated**: 2024-05-15  
**Status**: ✅ Production Ready
