# 🚦 Giám sát lưu lượng giao thông (Traffic Flow Monitoring)

## Tổng quan hệ thống

Hệ thống này sử dụng **AI/ML (YOLOv8)** để theo dõi và phân tích lưu lượng giao thông từ video.

---

## 📊 Các chỉ số chính

### 1. **Lưu lượng xe (Flow Rate)**
- **Định nghĩa:** Số lượng xe qua điểm quan sát trong một khoảng thời gian
- **Đơn vị:** Xe/phút (vehicles/minute)
- **Tính toán:** Đếm số xe vượt qua đường trong mỗi khung thời gian
- **Ý nghĩa:** 
  - Flow cao = Giao thông tắc
  - Flow thấp = Giao thông thông thoáng

### 2. **Lưu lượng trung bình (Average Flow Rate)**
- **Định nghĩa:** Trung bình lưu lượng trong toàn bộ thời gian giám sát
- **Ứng dụng:** Đánh giá mức độ kẹt xe trung bình trong khoảng thời gian

### 3. **Lưu lượng cao nhất (Peak Flow Rate)**
- **Định nghĩa:** Giá trị lưu lượng cao nhất được ghi nhận
- **Ứng dụng:** Xác định khoảng thời gian cao điểm kẹt xe

### 4. **Mật độ giao thông (Traffic Density)**
- **Định nghĩa:** Tỷ lệ % chiều rộng đường bị chiếm bởi các xe
- **Đơn vị:** % (0-100%)
- **Tính toán:** 
  ```
  Density = (Tổng chiều rộng bounding box) / (Số xe × Chiều rộng frame) × 100
  ```
- **Giải thích:**
  - 0-20%: Rất ít xe
  - 20-40%: Nhẹ
  - 40-70%: Vừa phải
  - 70-90%: Kẹt
  - >90%: Rất kẹt

### 5. **Mức độ kẹt xe (Congestion Level)**
- **Định nghĩa:** Mức độ tắc nghẽn giao thông dựa trên nhiều yếu tố
- **Các mức độ:**
  - `FREE` - Thông thoáng ✅
  - `LIGHT` - Nhẹ 🟢
  - `MODERATE` - Vừa phải 🟡
  - `HEAVY` - Kẹt 🟠
  - `VERY_HEAVY` - Rất kẹt 🔴

- **Cách tính:**
  ```
  if flow_rate < 5 AND total_vehicles > 20:
      → VERY_HEAVY (Rất kẹt)
  elif avg_flow < 10 OR total_vehicles > 15:
      → HEAVY (Kẹt)
  elif avg_flow < 20 OR total_vehicles > 8:
      → MODERATE (Vừa)
  elif avg_flow < 30:
      → LIGHT (Nhẹ)
  else:
      → FREE (Thông)
  ```

### 6. **Chi tiết theo loại xe**
- **Xe hơi** (Cars) 🚗
- **Xe máy** (Motorcycles) 🏍️
- **Xe buýt** (Buses) 🚌
- **Xe tải** (Trucks) 🚚
- **Xe đạp** (Bicycles) 🚲

Mỗi loại được tính riêng: Tổng qua + (Vào + Ra)

---

## 🎯 Cách sử dụng giao diện web

### Tab 1: UPLOAD VIDEO
1. Chọn video muốn giám sát
2. Tùy chỉnh tham số (nếu cần)
3. Nhấp "UPLOAD & XỬ LÝ"
4. Chờ xử lý hoàn tất

### Tab 2: DANH SÁCH JOBS
- Xem danh sách video đang xử lý hoặc đã xong
- Theo dõi tiến độ
- Download hoặc xem chi tiết

### Tab 3: KẾT QUẢ
- 📊 Lưu lượng xe (xe/phút)
- 📈 Lưu lượng cao nhất
- 🚦 Mức kẹt xe
- 🎯 Mật độ giao thông
- 🚗 Chi tiết từng loại xe

---

## ⚙️ Tham số tùy chỉnh

### 1. **Ngưỡng tin cậy (Confidence)**
- **Phạm vi:** 0-1
- **Mặc định:** 0.4
- **Ý nghĩa:** Độ tự tin của mô hình trong việc phát hiện xe
- **Tăng → Chỉ phát hiện xe rõ ràng hơn (bỏ qua xe mờ)**
- **Giảm → Phát hiện nhiều xe hơn (nhưng có thể sai)**

### 2. **Ngưỡng IoU (Intersection over Union)**
- **Phạm vi:** 0-1
- **Mặc định:** 0.45
- **Ý nghĩa:** Tiêu chuẩn loại bỏ các phát hiện trùng lặp
- **Tăng → Loại bỏ nhiều trùng lặp (chỉ giữ tốt nhất)**
- **Giảm → Giữ nhiều phát hiện hơn (có thể bị trùng lặp)**

### 3. **Vị trí đường quan sát (Line Ratio)**
- **Phạm vi:** 0.1-0.9
- **Mặc định:** 0.5 (giữa frame)
- **Ý nghĩa:** Vị trí của đường quan sát (từ trên xuống dưới)
- **0.2 → Đường ở 1/5 từ trên**
- **0.5 → Đường ở giữa**
- **0.8 → Đường ở 4/5 từ trên**

---

## 💡 Ứng dụng thực tế

### 1. **Giám sát giao thông thành phố**
- Theo dõi lưu lượng xe trên các tuyến đường chính
- Phát hiện tắc đường tự động
- Hỗ trợ quyết định điều tiết giao thông

### 2. **Quản lý bãi đỗ**
- Theo dõi số xe vào/ra
- Cảnh báo khi gần đầy
- Tính doanh thu

### 3. **Phân tích mô hình giao thông**
- Xác định giờ cao điểm
- Phân tích hành vi lái xe
- Tối ưu hóa luồng giao thông

### 4. **An toàn giao thông**
- Phát hiện giao thông bất thường
- Theo dõi tốc độ xe
- Cảnh báo tai nạn

---

## 📈 Biểu đồ & Thống kê

Hệ thống lưu trữ:
- **Lưu lượng theo thời gian** (lịch sử 1 giờ)
- **Thống kê theo loại xe**
- **Mật độ giao thông**
- **Mức kẹt xe**

Dữ liệu có thể:
- ✅ Xuất sang JSON để phân tích tiếp
- ✅ Visualize thành biểu đồ
- ✅ Tích hợp với hệ thống thông minh khác

---

## 🔧 Cấu hình nâng cao

### Trong `counter.py`:

```python
# Tăng độ chính xác theo dõi
offset = 6  # Vùng buffer quanh đường (pixel)

# Lưu trữ lịch sử
maxlen = 3600  # Giữ 1 giờ dữ liệu (tùy chỉnh)
```

### Trong `app.py`:

```python
# Tăng độ tin cậy phát hiện
confidence = 0.4  # Tăng lên 0.6+ để chỉ phát hiện rõ ràng

# Chọn GPU
device = "0"  # GPU ID (thay vì "cpu")
```

---

## 🚀 Tối ưu hiệu suất

### 1. **Giảm độ phân giải video**
- Video độ phân giải thấp → Xử lý nhanh hơn
- Nhưng mất độ chính xác

### 2. **Dùng model nhẹ hơn**
- `yolov8n.pt` (nhẹ, nhanh) ← Mặc định
- `yolov8m.pt` (cân bằng)
- `yolov8l.pt` (nặng, chính xác hơn)

### 3. **Sử dụng GPU**
- GPU xử lý 10-100x nhanh hơn CPU
- Yêu cầu NVIDIA GPU + CUDA

---

## ❓ FAQ

**Q: Cách tính lưu lượng chính xác?**  
A: Lưu lượng = (Số xe qua đường trong T giây) × (60 / T)

**Q: Mục đích của "offset"?**  
A: Tránh đếm lặp lại khi xe chậm qua đường (6px mặc định)

**Q: Video phải bao lâu?**  
A: Không có giới hạn, nhưng video lâu → xử lý lâu hơn

**Q: Có thể giám sát multiple lanes?**  
A: Hiện tại chỉ 1 lane, có thể mở rộng bằng multiple counters

**Q: Độ chính xác là bao nhiêu?**  
A: Tùy theo điều kiện ánh sáng, khoảng 85-95% trong điều kiện tốt

---

**Enjoy the Traffic Flow Monitoring System! 🚦**
