# 📹 Hướng dẫn Phân tích Video Trực tiếp (Live Stream)

## 📚 Tổng quan

Tính năng **Phân tích Video Trực tiếp** cho phép bạn:
- **Phân tích webcam trực tiếp** trong thời gian thực (real-time)
- **Phát hiện xe** từ camera của máy tính
- **Giám sát lưu lượng giao thông** live
- **Phát hiện vi phạm vượt đèn đỏ** trong real-time
- **Xem thống kê tức thì** không cần chờ xử lý video

## 🚀 Cách sử dụng

### Bước 1: Khởi động hệ thống
```bash
python app.py
```

### Bước 2: Truy cập web interface
Mở trình duyệt và vào: **http://localhost:5000**

### Bước 3: Chọn tab "📹 PHÂN TÍCH TRỰC TIẾP"
Nhấp vào tab **"📹 PHÂN TÍCH TRỰC TIẾP"** trên giao diện web

### Bước 4: Điều chỉnh tham số (tùy chọn)
```
- Ngưỡng tin cậy: 0.40 (40% confidence)
- Ngưỡng IoU: 0.45 (45% IOU)
- Vị trí đường đếm: 0.50 (giữa frame)
```

### Bước 5: Nhấp "▶️ BẮT ĐẦU TRỰC TIẾP"
Hệ thống sẽ:
- Kết nối đến webcam
- Bắt đầu phát hiện xe
- Hiển thị video live trên màn hình
- Cập nhật thống kê real-time

### Bước 6: Xem kết quả
Video trực tiếp sẽ hiển thị:
- ✅ Bounding boxes xung quanh xe
- ✅ Track ID cho từng xe
- ✅ Đường đếm (counting line)
- ✅ Biểu tượng đèn giao thông (RED/YELLOW/GREEN)
- ✅ Thông tin vi phạm (nếu có)

### Bước 7: Dừng stream
Nhấp nút "⏹️ DỪNG" để kết thúc phân tích trực tiếp

## 📊 Thống kê Trực tiếp

Khi stream đang chạy, bạn sẽ thấy:

### 1. **Lưu lượng (xe/phút)**
- Số lượng xe qua đường mỗi phút
- Cập nhật tức thì

### 2. **Xe trên đường**
- Số xe hiện đang nhìn thấy trong frame
- Thay đổi liên tục

### 3. **Vi phạm**
- Số lần xe vượt đèn đỏ
- Được cập nhật khi phát hiện

### 4. **Tổng xe vào**
- Tổng số xe qua đường từ khi bắt đầu

## ⚙️ Tham số điều chỉnh

### Ngưỡng tin cậy (Confidence)
- **Thấp (0.3)**: Phát hiện nhiều xe, nhưng có thể có sai lệch
- **Cao (0.7)**: Phát hiện chính xác nhưng có thể bỏ sót

**Khuyến nghị**: `0.4 - 0.5`

### Ngưỡng IoU
- Dùng để loại bỏ detection trùng lặp
- **Thấp (0.3)**: Giữ lại nhiều detection
- **Cao (0.7)**: Loại bỏ nhiều detection

**Khuyến nghị**: `0.45`

### Vị trí đường đếm (Line Ratio)
- Vị trí Y trên frame (từ 0 = trên cùng đến 1 = dưới cùng)
- **0.3**: Phía trên
- **0.5**: Giữa (mặc định)
- **0.7**: Phía dưới

**Khuyến nghị**: `0.5` (giữa frame)

## 🎥 API Streaming

### Route: `/api/stream/start` (POST)
**Bắt đầu stream từ webcam**

```json
{
  "camera": 0,
  "confidence": 0.4,
  "iou": 0.45,
  "line_ratio": 0.5
}
```

### Route: `/api/stream/stop` (POST)
**Dừng stream**

```bash
curl -X POST http://localhost:5000/api/stream/stop
```

### Route: `/api/stream/video_feed` (GET)
**Lấy video stream dưới dạng MJPEG**

```
http://localhost:5000/api/stream/video_feed?confidence=0.4&iou=0.45&line_ratio=0.5
```

### Route: `/api/stream/stats` (GET)
**Lấy thống kê hiện tại**

```json
{
  "flow_rate": 12.5,
  "total_vehicles_in": 45,
  "total_vehicles_out": 40,
  "violations": {
    "total_violations": 2,
    "severe_violations": 0,
    "moderate_violations": 1,
    "minor_violations": 1
  }
}
```

## 🔧 Khắc phục sự cố

### Webcam không được phát hiện
- Kiểm tra xem camera có được kết nối không
- Thử `camera_index = 1` hoặc `2` nếu có nhiều camera

### Video stream bị lag
- Giảm confidence threshold
- Tăng độ nén JPEG (giảm quality từ 80 xuống 70)

### Không thấy detection boxes
- Tăng confidence threshold thấp hơn (ví dụ 0.3)
- Kiểm tra có xe trong frame không
- Đảm bảo ánh sáng đủ

### Frame rate thấp
- Giảm resolution (trong generate_stream_frames)
- Tăng IOU threshold
- Giảm độ phức tạp khác

## 📈 Tối ưu hiệu suất

### Để có FPS cao:
1. Giảm **Confidence** xuống ~0.3
2. Tăng **IOU** lên ~0.6
3. Giảm **JPEG Quality** xuống 60-70
4. Dùng **resolution 1280x720** thay vì 1920x1080

### Để có chính xác cao:
1. Tăng **Confidence** lên ~0.6
2. Giữ **IOU** ở 0.45-0.55
3. Tăng **JPEG Quality** lên 85-90
4. Dùng **resolution 1920x1080**

## 🌐 Tích hợp với ứng dụng khác

Bạn có thể tích hợp stream vào các ứng dụng khác:

```html
<!-- Nhúng stream vào trang HTML -->
<img src="http://localhost:5000/api/stream/video_feed?confidence=0.4&iou=0.45&line_ratio=0.5" 
     style="width: 100%; height: auto;" />
```

```python
# Lấy thống kê từ Python
import requests

stats = requests.get('http://localhost:5000/api/stream/stats').json()
print(f"Flow rate: {stats['flow_rate']} vehicles/min")
print(f"Violations: {stats['violations']['total_violations']}")
```

## 📝 Ghi chú

- **Chu kỳ đèn**: Được mô phỏng tự động (GREEN 10s, YELLOW 3s, RED 10s)
- **Tốc độ xe**: Được tính từ sự thay đổi vị trí giữa các frame
- **Không cần GPU**: Chạy trên CPU, nhưng chậm hơn với GPU

## 🎉 Ưu điểm

✅ Phân tích **real-time** không delay  
✅ **Không cần upload** video (cực nhanh)  
✅ **Xem kết quả tức thì** trên màn hình  
✅ Có thể **điều chỉnh tham số** ngay trong quá trình chạy  
✅ **CPU-friendly** (chạy được trên máy yếu)  
✅ **API đơn giản** để tích hợp  

---

**Bản quyền**: Hệ thống Phân tích Video Giao thông (Traffic Analysis System)  
**Phiên bản**: 1.0  
**Cập nhật**: 2024
