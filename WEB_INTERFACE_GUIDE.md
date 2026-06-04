# 🌐 Hướng dẫn sử dụng Web Interface

## Thay đổi chính

Thay vì chạy camera trực tiếp, hệ thống giờ có **giao diện web** cho phép:
- ✅ **Upload video** từ trình duyệt
- ✅ **Xử lý video** trong nền (background processing)
- ✅ **Xem tiến độ** real-time
- ✅ **Download video** đã xử lý
- ✅ **Xem thống kê chi tiết** (xe vào, xe ra, loại xe, v.v.)

---

## 📥 Cài đặt

### 1. Cài đặt Dependencies

```bash
# Activate virtual environment (nếu có)
venv\Scripts\activate  # Windows

# Cài tất cả thư viện cần thiết
pip install -r requirements.txt
```

**Các thư viện mới được thêm:**
- `flask>=2.3.0` - Web framework
- `werkzeug>=2.3.0` - WSGI utility

---

## 🚀 Khởi động Web Server

### Cách 1: Sử dụng script (Windows)
```bash
# Double-click file này hoặc chạy trong Terminal
start_web_server.bat
```

### Cách 2: Chạy trực tiếp Python
```bash
python app.py
```

### Cách 3: Chạy với debug mode (phát triển)
```bash
python app.py --debug
```

---

## 🌍 Truy cập Web Interface

Sau khi khởi động server, mở trình duyệt và truy cập:

```
http://localhost:5000
```

---

## 📤 Hướng dẫn sử dụng

### Tab 1: UPLOAD VIDEO

1. **Kéo thả video** vào vùng upload hoặc **nhấp để chọn file**
   - Hỗ trợ: MP4, AVI, MOV, MKV (max 500MB)

2. **Tùy chỉnh tham số xử lý:**
   - **Ngưỡng tin cậy (Confidence):** 0-1 (mặc định 0.4)
   - **Ngưỡng IoU:** 0-1 (mặc định 0.45)
   - **Sức chứa bãi đỗ:** Số xe (mặc định 50)
   - **Vị trí đường đếm:** 0.1-0.9 (mặc định 0.5 = giữa frame)

3. **Nhấp "UPLOAD & XỬ LÝ"**
   - Video được upload
   - Xử lý bắt đầu (có thể mất vài phút tùy theo độ dài video)

4. **Theo dõi tiến độ:**
   - Thanh progress hiển thị % hoàn thành
   - Server xử lý trong background

---

### Tab 2: DANH SÁCH JOBS

Xem danh sách tất cả các video đã upload/đang xử lý:

- **Tên file** - Tên video được upload
- **Trạng thái** - queued | processing | completed | error
- **Progress** - % hoàn thành
- **Hành động:**
  - 📥 **Download** - Tải video xử lý xong
  - 📊 **Chi tiết** - Xem kết quả thống kê

Nhấp **"🔄 Làm mới"** để cập nhật danh sách

---

### Tab 3: KẾT QUẢ

Xem chi tiết kết quả xử lý của từng video:

**Thống kê:**
- 📊 **Tổng Frames** - Số frame trong video
- **FPS** - Frames per second
- **Độ dài video** - Thời gian video (giây)
- 🚗 **Xe vào** - Tổng số xe vào bãi
- 🚗 **Xe ra** - Tổng số xe ra khỏi bãi
- 🚗 **Xe hiện tại** - Số xe đang trong bãi
- 📦 **Sức chứa** - Tổng sức chứa bãi đỗ

**Chi tiết loại xe:**
- Số lượng xe hơi, xe máy, xe buýt, xe tải, xe đạp
- Tách riêng theo chiều vào/ra

---

## 📁 Cấu trúc file

```
project_root/
├── app.py                    # Flask web server
├── templates/
│   └── dashboard.html        # Web interface
├── uploads/                  # Thư mục chứa video upload
│   └── [timestamp]_[filename].mp4
├── outputs/                  # Thư mục chứa kết quả
│   ├── [job_id]_processed.mp4     # Video xử lý xong
│   └── [job_id]_stats.json        # Thống kê (JSON)
└── ...
```

---

## 🔧 Cấu hình Flask

File `app.py` chứa các cấu hình:

```python
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # Max upload: 500MB
app.config['UPLOAD_FOLDER'] = 'uploads'               # Thư mục upload
app.config['OUTPUT_FOLDER'] = 'outputs'               # Thư mục output
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}
```

---

## 📊 API Endpoints

Nếu muốn tích hợp với ứng dụng khác:

| Endpoint | Phương thức | Mô tả |
|----------|------------|-------|
| `/` | GET | Trang chính |
| `/api/upload` | POST | Upload video |
| `/api/status/<job_id>` | GET | Trạng thái job |
| `/api/download/<job_id>` | GET | Download video |
| `/api/results/<job_id>` | GET | Kết quả thống kê (JSON) |
| `/api/jobs` | GET | Danh sách tất cả jobs |

**Ví dụ:**

```bash
# Kiểm tra trạng thái
curl http://localhost:5000/api/status/job_20260515_120000_abc123

# Lấy kết quả thống kê
curl http://localhost:5000/api/results/job_20260515_120000_abc123
```

---

## ⚠️ Ghi chú quan trọng

1. **Lần đầu chạy:**
   - Model YOLOv8 sẽ được download (khoảng 100-200MB)
   - Xử lý frame đầu tiên có thể chậm hơn

2. **Performance:**
   - Xử lý video phụ thuộc vào độ dài, độ phân giải, và CPU
   - Khuyến nghị sử dụng GPU nếu có (chỉnh `device='0'` trong detector)

3. **Lưu trữ:**
   - Video upload/output lưu trên disk (có thể xóa thủ công)
   - Định kỳ xóa video cũ để tiết kiệm dung lượng

---

## 🐛 Troubleshooting

### Port 5000 bị chiếm dụng
```bash
# Windows - Tìm process sử dụng port 5000
netstat -ano | findstr :5000

# Tìm PID và kill process
taskkill /PID [PID] /F
```

### Flask không cài đặt
```bash
pip install flask werkzeug
```

### Video không xử lý được
- Kiểm tra định dạng video hỗ trợ
- Kiểm tra OpenCV có decode được video không
- Xem log server để tìm lỗi chi tiết

---

## 📞 Hỗ trợ

Nếu gặp vấn đề, kiểm tra:
1. Terminal có lỗi nào không?
2. Browser console (F12) có warning?
3. File `uploads/` và `outputs/` có quyền ghi không?

---

**Enjoy the new web interface! 🎉**
