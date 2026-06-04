# 🚀 BLOCKCHAIN & METAMASK - QUICK START GUIDE

## ⚡ 5 Phút để Bắt Đầu

### 📝 Bước 1: Cài Đặt Dependencies (2 phút)

```bash
# Activate environment
python -m venv .venv
.\.venv\Scripts\activate

# Cài packages
pip install -r requirements.txt
```

---

### 🔐 Bước 2: Chuẩn Bị MetaMask (1 phút)

1. **Cài MetaMask**: https://metamask.io
2. **Tạo wallet** (hoặc import existing)
3. **Switch sang Sepolia Testnet**:
   - Click network dropdown → "Sepolia test network"
4. **Lấy Private Key**:
   - Settings → Security & Privacy → "Show Private Key"
   - Copy key (cẩn thận: đừng share!)
5. **Lấy Testnet ETH**:
   - Sepolia Faucet: https://www.sepoliafaucet.io/
   - Paste address của bạn, request funds

---

### 📋 Bước 3: Deploy Smart Contract (1 phút)

1. **Mở**: https://remix.ethereum.org/
2. **File → New File** → `TrafficViolationRegistry.sol`
3. **Copy & paste** nội dung từ file `TrafficViolationRegistry.sol` (trong project)
4. **Click Solidity Compiler** → Compile
5. **Click Deploy & Run Transactions**:
   - Environment: "Injected Provider - MetaMask"
   - Kết nối MetaMask
   - Click "Deploy"
   - Confirm transaction trong MetaMask popup
6. **Copy contract address** từ console

---

### ⚙️ Bước 4: Cấu Hình .env (1 phút)

Tạo file `.env` trong project root:

```env
BLOCKCHAIN_NETWORK=sepolia
VIOLATION_CONTRACT_ADDRESS=0x[PASTE_YOUR_CONTRACT_ADDRESS]
PRIVATE_KEY=0x[PASTE_YOUR_PRIVATE_KEY]
METAMASK_NETWORK_ID=11155111
TESTNET_FAUCET_URL=https://www.sepoliafaucet.io/
```

⚠️ **Lưu ý**: Không share .env file!

---

### ✅ Bước 5: Test Connection (0 phút)

```python
# test_blockchain_quick.py
from blockchain import blockchain_manager

# Check status
status = blockchain_manager.get_network_status()
print("✓ Blockchain Status:", status)

# Check balance
balance = blockchain_manager.get_account_balance()
print(f"✓ Account Balance: {balance} ETH")
```

**Chạy**:
```bash
python test_blockchain_quick.py
```

✅ Nếu không có lỗi → Thành công!

---

## 🎯 Bây Giờ Bạn Có Thể:

### ✨ Ghi Vi Phạm lên Blockchain

**Backend (Python)**:
```python
from blockchain import blockchain_manager

result = blockchain_manager.record_violation(
    vehicle_id="29A123456",
    violation_type="red_light",
    severity="severe",
    location="12.9716,77.5946",
    image_hash="QmXyZ..."
)

print(f"✓ Transaction: {result['tx_hash']}")
```

**Frontend (JavaScript)**:
```javascript
// Kết nối MetaMask
await metamask.connect();

// Ghi vi phạm
const tx = await metamask.recordViolation(
    "29A123456",      // Vehicle ID
    "red_light",      // Type
    "severe",         // Severity
    "12.9716,77.5946", // Location
    "QmXyZ..."        // Image Hash
);

console.log("✓ Transaction:", tx.tx_hash);
```

### 🔍 Lấy Vi Phạm của Xe

**Backend**:
```python
violations = blockchain_manager.get_vehicle_violations("29A123456")
for v in violations:
    print(f"{v['violation_type']} - {v['severity']}")
```

**Frontend**:
```javascript
const violations = await metamask.getVehicleViolations("29A123456");
violations.forEach(v => {
    console.log(`${v.violation_type}: ${v.severity}`);
});
```

### 💰 Kiểm Tra Số Dư

```javascript
const balance = await metamask.getBalance();
console.log(`Số dư: ${balance} ETH`);
```

---

## 🔗 API Endpoints Chính

| Endpoint | Method | Mô Tả |
|----------|--------|-------|
| `/api/blockchain/status` | GET | Lấy trạng thái blockchain |
| `/api/blockchain/record-violation` | POST | Ghi vi phạm |
| `/api/blockchain/violations/{id}` | GET | Lấy vi phạm của xe |
| `/api/metamask/status` | GET | Trạng thái MetaMask |
| `/api/metamask/connect` | POST | Kết nối MetaMask |

---

## 🚨 Troubleshooting

### ❌ "Connection failed"
```
→ Kiểm tra internet connection
→ Kiểm tra BLOCKCHAIN_NETWORK trong .env
→ Kiểm tra RPC endpoint
```

### ❌ "Invalid private key"
```
→ Format: 0x + 64 hex characters
→ Example: 0xabcd1234...
```

### ❌ "MetaMask not detected"
```
→ Kiểm tra MetaMask extension đã cài
→ Kiểm tra browser support
→ Refresh page
```

### ❌ "Insufficient gas"
```
→ Lấy thêm testnet ETH từ faucet
→ Sepolia: https://www.sepoliafaucet.io/
```

---

## 📚 Tài Liệu Đầy Đủ

Xem chi tiết tại: **BLOCKCHAIN_SETUP_GUIDE.md**

---

## 🎓 Tiếp Theo

1. ✅ Deploy smart contract ✓
2. ✅ Test blockchain connection ✓
3. ⏳ Integrate vào web interface
4. ⏳ Implement violation recording
5. ⏳ Setup IPFS cho image hashing (optional)

---

## 💬 Hỗ Trợ

Nếu gặp lỗi:
1. Kiểm tra console logs
2. Đọc BLOCKCHAIN_SETUP_GUIDE.md
3. Verify .env configuration
4. Check testnet ETH balance

---

**Ready to go!** 🚀
