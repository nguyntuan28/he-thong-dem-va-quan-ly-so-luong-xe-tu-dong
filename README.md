![Poster dự án](nguyntuan.jpg)
# 🚗 Traffic Flow Monitoring System — YOLOv8 + Violation Detection

Hệ thống giám sát lưu lượng giao thông tự động sử dụng **YOLOv8** + **OpenCV** + **Violation Detection** + **Evidence Photos**.

**🎉 Version 2.2 - WITH VIOLATION IMAGE VIEWER** ⭐

---

## 📁 Cấu trúc dự án

```
project/
├── app.py                # Flask web server + API
├── detector.py           # YOLOv8 vehicle detector + tracker
├── counter.py            # Traffic flow calculations
├── red_light_detector.py # Violation detection + image capture ⭐
├── manager.py            # Job queue management
├── hud.py                # HUD overlay renderer
├── requirements.txt      # Python dependencies
├── yolov8n.pt            # AI model (auto-downloads)
├── templates/
│   └── dashboard.html    # Web UI (4 tabs, 4 modals)
├── uploads/              # Uploaded videos
├── outputs/              # Processed results
│   ├── job_xxx_processed.mp4
│   ├── job_xxx_stats.json
│   └── job_xxx_violations/ ⭐ (violation photos)
├── README.md             # This file
├── QUICK_START.md        # Setup guide
├── VIOLATION_IMAGE_VIEWER.md  # Photo viewer feature
├── FEATURES_COMPLETE.md  # All features list
└── THAY_DOI.txt          # Vietnamese changelog
```

---

## ⚙️ Cài đặt

```bash
# 1. Tạo virtualenv (khuyến nghị)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Cài thư viện
pip install -r requirements.txt
```

---

## 🚀 Cách chạy

### 🌐 Chế độ WEB (ĐỀ XUẤT)
```bash
python app.py
```
Mở trình duyệt: **http://localhost:5000**

**4 Tabs trên Dashboard:**

- ✅ **Tab 1: 📤 UPLOAD**
  - Upload video từ giao diện web
  - Xử lý video trong background
  - Modal phân tích trực tiếp (see video + progress)
  - Download video đã xử lý

- ✅ **Tab 2: 📹 LIVE**
  - Phân tích từ webcam trong real-time
  - Live stats cập nhật mỗi frame
  - Start/Stop webcam buttons

- ✅ **Tab 3: ✅ RESULTS**
  - Danh sách tất cả jobs
  - Status badges (queued/processing/completed/error)
  - Download & Chi tiết buttons

- ✅ **Tab 4: 📋 CHI TIẾT**
  - **Thống kê giao thông (8 cards):**
    - 📊 Lưu lượng hiện tại (xe/phút)
    - 📊 Lưu lượng trung bình (1 giờ)
    - 📈 Lưu lượng cao nhất (1 giờ)
    - 🎯 Mật độ giao thông (%)
    - 🚦 Mức độ kẹt xe (FREE/LIGHT/MODERATE/HEAVY/VERY_HEAVY)
    - 🚗 Tổng xe đếm được
    - 📍 Xe dừng ở line
    - 📐 Vị trí line (%)
    
  - **Thống kê vi phạm (5 cards):**
    - 🚨 Tổng vi phạm
    - 🔴 Vi phạm SEVERE (đỏ - tốc độ cao)
    - 🟠 Vi phạm MODERATE (cam - tốc độ vừa)
    - 🟡 Vi phạm MINOR (vàng - tốc độ thấp)
    - 🚗 Xe vi phạm unique
    
  - **📋 Vi phạm gần đây - CLICK TO VIEW PHOTOS ⭐**
    - Danh sách tối đa 10 vi phạm gần nhất
    - **Click bất kỳ dòng nào → Modal mở**
    - Modal hiển thị:
      - ✅ **Ảnh xe vi phạm** (cropped, JPEG)
      - ✅ **Loại xe** (car, motorcycle, bus, truck, bicycle)
      - ✅ **Mức độ** (SEVERE/MODERATE/MINOR - color-coded)
      - ✅ **Thời gian** (HH:MM:SS)
      - ✅ **Track ID** (ID xe)
      - ✅ **Frame number** (frame nào xảy ra)

---

## 📊 Các chỉ số giám sát

| Chỉ số | Giải thích |
|--------|-----------|
| **Lưu lượng (Flow Rate)** | Số xe qua điểm quan sát / phút |
| **Lưu lượng TB (Avg Flow)** | Trung bình lưu lượng trong toàn video |
| **Lưu lượng cao nhất (Peak Flow)** | Lưu lượng cao nhất được ghi nhận |
| **Mật độ giao thông** | Tỷ lệ % chiều rộng đường bị chiếm bởi xe |
| **Mức kẹt xe** | FREE (thông), LIGHT (nhẹ), MODERATE (vừa), HEAVY (kẹt), VERY_HEAVY (rất kẹt) |

---

## 🎯 Ứng dụng thực tế

- 🚦 Giám sát giao thông trên đường
- 📍 Phát hiện tình trạng kẹt xe
- 📊 Thu thập dữ liệu lưu lượng giao thông
- 🚗 Quản lý bãi đỗ xe
- 🔍 Phân tích mô hình giao thông
- **⭐ 🚨 Phát hiện vi phạm vượt đèn đỏ với chứng cứ ảnh**

---

## 🔴 Red Light Violation Detection (NEW!)

**Tính năng mới:** Tự động phát hiện xe vượt đèn đỏ và **lưu ảnh chứng cứ**

### Cách hoạt động
1. Mô phỏng chu kỳ đèn: GREEN (10s) → YELLOW (3s) → RED (10s)
2. Khi RED: Phát hiện xe vượt đường kẻ
3. Tính tốc độ: pixels/frame (từ tracking)
4. Phân loại mức độ vi phạm:
   - 🔴 **SEVERE**: tốc độ > 15 px/frame (vi phạm nặng)
   - 🟠 **MODERATE**: tốc độ 8-15 px/frame (vi phạm vừa)
   - 🟡 **MINOR**: tốc độ < 8 px/frame (vi phạm nhẹ)

### Lưu trữ ảnh chứng cứ
- ✅ Crop frame quanh xe vi phạm (±10px)
- ✅ Lưu JPEG 85% quality
- ✅ Đặt tên theo index & mức độ:
  - `violation_000_severe.jpg`
  - `violation_001_moderate.jpg`
  - `violation_002_minor.jpg`
- ✅ Có thể xem bằng cách click vào danh sách violations

### Viewing Evidence Photos
- Vào Tab "📋 CHI TIẾT"
- Cuộn xuống "📋 Vi phạm gần đây"
- Click bất kỳ dòng nào
- Modal mở với ảnh + thông tin đầy đủ

---

## 🎯 Ứng dụng thực tế

- 🚦 Giám sát giao thông trên đường
- 📍 Phát hiện tình trạng kẹt xe
- 📊 Thu thập dữ liệu lưu lượng giao thông
- 🚗 Quản lý bãi đỗ xe
- 🔍 Phân tích mô hình giao thông

### Webcam thực tế
```bash
python app.py  # Web mode (MỚI, ĐỀ XUẤT)
```

### Cài đặt tham số trên giao diện web
- **Confidence**: Ngưỡng nhận diện (0.0-1.0)
- **IOU**: Overlap threshold (0.0-1.0)
- **Capacity**: Dùng để tính mật độ giao thông
- **Line Ratio**: Vị trí đường đếm (0.0-1.0)

---

## 🔌 API Endpoints (13 tổng cộng)

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/upload` | POST | Upload video |
| `/api/status/<job_id>` | GET | Kiểm tra status job |
| `/api/download/<job_id>` | GET | Tải video xử lý |
| `/api/results/<job_id>` | GET | Lấy thống kê |
| `/api/jobs` | GET | Danh sách tất cả jobs |
| `/api/stream/start` | POST | Bắt đầu webcam |
| `/api/stream/stop` | POST | Dừng webcam |
| `/api/stream/video_feed` | GET | MJPEG webcam |
| `/api/stream/stats` | GET | Webcam stats |
| `/api/stream/processing/<job_id>` | GET | MJPEG video đang xử lý |
| `/api/processing/stats/<job_id>` | GET | Live processing stats |
| `/api/violation/image/<job_id>/<id>` | GET | **Lấy ảnh vi phạm** ⭐ |
| `/api/violations/<job_id>` | GET | **Danh sách violations** ⭐ |

---

## 📊 Tính năng

| Tính năng | Mô tả |
|-----------|-------|
| **Phát hiện xe** | YOLOv8 nhận diện 5 loại: xe hơi, xe máy, xe buýt, xe tải, xe đạp |
| **Theo dõi (tracking)** | ByteTracker tích hợp — theo dõi liên tục theo track_id |
| **Giám sát lưu lượng** | Flow rate, mật độ, mức độ kẹt (5 levels) |
| **Phát hiện vi phạm** | ⭐ Vượt đèn đỏ tự động (SEVERE/MODERATE/MINOR) |
| **Lưu ảnh chứng cứ** | ⭐ Crop frame xe vi phạm, lưu JPEG |
| **Web dashboard** | 4 tabs, 4 modals, real-time stats |
| **Upload video** | Hỗ trợ 6 format, max 500MB |
| **Webcam streaming** | MJPEG real-time live analysis |
| **HUD overlay** | Thông tin thống kê hiện lên frame video |
| **Báo cáo JSON** | Lưu thống kê & violations với image paths |

---

## 🎯 Các model YOLOv8

| Model | Kích thước | mAP50 | Tốc độ (CPU) | Gợi ý dùng |
|-------|-----------|-------|-------------|-----------|
| yolov8n.pt | 6.3 MB | 37.3 | Nhanh nhất | Demo, thiết bị yếu |
| yolov8s.pt | 21.5 MB | 44.9 | Trung bình | **Khuyến nghị** |
| yolov8m.pt | 49.7 MB | 50.2 | Chậm hơn | Cần GPU |
| yolov8l.pt | 83.7 MB | 52.9 | Chậm | GPU bắt buộc |

Model sẽ tự động tải về lần đầu chạy.

---

## � Documentation

Các tài liệu chi tiết có sẵn:

- **[QUICK_START.md](QUICK_START.md)** - 🚀 Hướng dẫn cài đặt & chạy nhanh
- **[VIOLATION_IMAGE_VIEWER.md](VIOLATION_IMAGE_VIEWER.md)** - 🖼️ Hướng dẫn xem ảnh vi phạm chi tiết
- **[FEATURES_COMPLETE.md](FEATURES_COMPLETE.md)** - ✅ Danh sách đầy đủ tất cả tính năng
- **[THAY_DOI.txt](THAY_DOI.txt)** - 📝 Changelog tiếng Việt

---

## 🚀 Bắt đầu nhanh

```bash
# 1. Cài dependencies
pip install -r requirements.txt

# 2. Chạy Flask server
python app.py

# 3. Mở browser
# http://localhost:5000
```

**Sau ~2 giây sẽ thấy giao diện web!**

---

## 🎓 Ví dụ sử dụng

### Upload video từ giao diện
1. Chọn file video (mp4, avi, mov, mkv, flv, wmv)
2. Adjust parameters (confidence, IOU, capacity, line_ratio)
3. Click "🚀 UPLOAD & PROCESS"
4. Xem live video processing trong modal
5. Xem results trên tab "✅ RESULTS"
6. Click violations để xem ảnh chứng cứ

### Phân tích webcam live
1. Tab "📹 LIVE"
2. Click "📷 Start Webcam"
3. Xem real-time detections + stats
4. Click "⏹️ Stop Webcam" để dừng

### Export evidence photos
1. Xem violations trên Tab "📋 CHI TIẾT"
2. Click violations để mở modal
3. Right-click ảnh → Save As...
4. Dùng cho báo cáo/phạt

---

## 📊 Yêu cầu hệ thống

| Thành phần | Yêu cầu |
|-----------|--------|
| **OS** | Windows, macOS, Linux |
| **Python** | 3.8+ |
| **RAM** | 4GB (8GB recommended) |
| **Disk** | 2GB |
| **GPU** | Optional (CPU works) |
| **Camera** | Optional (for webcam feature) |

---

## 🐛 Troubleshooting

| Lỗi | Giải pháp |
|-----|----------|
| `ModuleNotFoundError` | Chạy: `pip install -r requirements.txt` |
| Không kết nối localhost:5000 | Chắc chắn Flask đang chạy (terminal phải có "Running on http://...") |
| Webcam không hoạt động | Kiểm tra camera được kết nối và cấp quyền |
| Video processing chậm | Giảm video resolution hoặc skip frames |
| Không thấy ảnh vi phạm | Chắc chắn violations có, check `outputs/<job_id>_violations/` folder |

---

## 🎉 Hoàn tất!

**System Status**: ✅ Production Ready  
**Version**: 2.2 with Violation Image Viewer  
**Total Features**: 20+  
**API Endpoints**: 13  
**Supported Formats**: 6 video formats  
**Max Upload**: 500MB  

---

## 📞 Support

Nếu gặp vấn đề:
1. Xem QUICK_START.md
2. Kiểm tra THAY_DOI.txt
3. Xem FEATURES_COMPLETE.md

---

**Made for Traffic Monitoring & Violation Detection** 🚦

Enjoy! 🚀

