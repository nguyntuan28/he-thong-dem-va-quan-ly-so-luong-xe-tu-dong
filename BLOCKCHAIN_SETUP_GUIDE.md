# 🔗 Hướng dẫn Tích hợp Blockchain & MetaMask

## 📋 Mục lục
1. [Chuẩn bị](#chuẩn-bị)
2. [Cài đặt](#cài-đặt)
3. [Deploy Smart Contract](#deploy-smart-contract)
4. [Cấu hình](#cấu-hình)
5. [Sử dụng](#sử-dụng)
6. [API Reference](#api-reference)

---

## 🔧 Chuẩn bị

### Yêu cầu cơ bản
- Python 3.8+
- MetaMask extension (cài từ https://metamask.io)
- Node.js 14+ (cho deploy smart contract)
- Hardhat hoặc Truffle (khuyến nghị: Hardhat)

### Accounts cần thiết
- **Ethereum Testnet Account** (Sepolia hoặc Mumbai)
- **Testnet ETH** (để thanh toán gas fees)
  - Sepolia Faucet: https://www.sepoliafaucet.io/
  - Mumbai Faucet: https://faucet.polygon.technology/

---

## 📦 Cài đặt

### 1. Cập nhật Dependencies

```bash
# Activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# hoặc
source .venv/bin/activate  # Linux/Mac

# Cài đặt packages
pip install -r requirements.txt
```

### 2. Cấu hình Environment

Tạo file `.env` từ template:

```bash
cp .env.example .env
```

Chỉnh sửa `.env`:

```env
# Blockchain network (sepolia hoặc polygon)
BLOCKCHAIN_NETWORK=sepolia

# Smart Contract Address (sau khi deploy)
VIOLATION_CONTRACT_ADDRESS=0x...

# Private Key (CHỈ CHO TESTING!)
# Lấy từ MetaMask: Settings > Security & Privacy > Show Private Key
PRIVATE_KEY=0x...

# Infura API Key (tùy chọn, nếu muốn sử dụng Infura)
INFURA_API_KEY=your_infura_key

# MetaMask Network ID
METAMASK_NETWORK_ID=11155111  # Sepolia: 11155111, Mumbai: 80001
```

### ⚠️ CẢNH BÁO BẢO MẬT
```
- KHÔNG chia sẻ .env file chứa PRIVATE_KEY
- KHÔNG commit .env vào git
- CHỈ dùng testnet ETH, không dùng mainnet
- Sử dụng dedicated wallet cho testing, không dùng ví chứa tiền thực
```

---

## 🚀 Deploy Smart Contract

### Phương pháp 1: Sử dụng Remix IDE (Khuyên dùng - Dễ nhất)

1. **Mở Remix IDE**: https://remix.ethereum.org/

2. **Tạo file mới**:
   - Click `File > New File`
   - Đặt tên: `TrafficViolationRegistry.sol`
   - Copy nội dung từ file `TrafficViolationRegistry.sol` trong project

3. **Compile Contract**:
   - Click `Solidity Compiler`
   - Chọn version `0.8.0+`
   - Click `Compile TrafficViolationRegistry.sol`

4. **Deploy**:
   - Click `Deploy & Run Transactions`
   - Chọn Environment: `Injected Provider - MetaMask`
   - Kết nối MetaMask (chọn Sepolia testnet)
   - Click `Deploy`
   - Confirm transaction trong MetaMask

5. **Lưu Contract Address**:
   - Sao chép địa chỉ contract
   - Paste vào file `.env` (VIOLATION_CONTRACT_ADDRESS)

### Phương pháp 2: Sử dụng Hardhat (Cho Dev)

```bash
# Tạo project Hardhat
npm init -y
npm install --save-dev hardhat

# Khởi tạo Hardhat project
npx hardhat

# Copy smart contract
cp TrafficViolationRegistry.sol contracts/

# Cập nhật hardhat.config.js
# Thêm network configuration cho Sepolia/Mumbai

# Deploy
npx hardhat run scripts/deploy.js --network sepolia
```

---

## ⚙️ Cấu hình

### 1. Khởi tạo Blockchain Manager

```python
from blockchain import blockchain_manager

# Manager sẽ tự động khởi tạo với network trong .env
# Hoặc chỉ định network:
from blockchain import BlockchainManager
blockchain_manager = BlockchainManager(network="sepolia")

# Lấy trạng thái
status = blockchain_manager.get_network_status()
print(status)
```

### 2. Kết nối Ví

**Phương pháp A: Từ Private Key (Backend)**

```python
# Từ file .env
import os
from dotenv import load_dotenv

load_dotenv()

private_key = os.getenv('PRIVATE_KEY')
contract_address = os.getenv('VIOLATION_CONTRACT_ADDRESS')

# Kết nối
blockchain_manager.connect_wallet(private_key, contract_address)
```

**Phương pháp B: Từ MetaMask (Frontend)**

JavaScript trong web interface:

```javascript
// Kết nối MetaMask
const metamask = new MetaMaskIntegration();
await metamask.connect();

// Kiểm tra trạng thái
console.log(metamask.isConnected);
console.log(metamask.account);
console.log(metamask.networkId);
```

---

## 💻 Sử dụng

### 1. Ghi Vi Phạm lên Blockchain

**Backend API**:

```bash
curl -X POST http://localhost:5000/api/blockchain/record-violation \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "29A123456",
    "violation_type": "red_light",
    "severity": "severe",
    "location": "12.9716,77.5946",
    "image_hash": "QmXyZ..."
  }'
```

**Frontend JavaScript**:

```javascript
// Kết nối MetaMask trước
await metamask.connect();

// Ghi vi phạm
const result = await metamask.recordViolation(
    "29A123456",      // Vehicle ID
    "red_light",      // Violation Type
    "severe",         // Severity
    "12.9716,77.5946", // Location (GPS)
    "QmXyZ..."        // Image Hash (IPFS)
);

console.log('Transaction:', result.tx_hash);
```

### 2. Lấy Vi Phạm của Xe

**Backend API**:

```bash
curl http://localhost:5000/api/blockchain/violations/29A123456
```

**Frontend JavaScript**:

```javascript
const violations = await metamask.getVehicleViolations("29A123456");

violations.forEach(v => {
    console.log(`
        Vehicle: ${v.vehicle_id}
        Type: ${v.violation_type}
        Severity: ${v.severity}
        Time: ${new Date(v.timestamp * 1000)}
    `);
});
```

### 3. Lấy Số Dư Tài Khoản

```javascript
const balanceETH = await metamask.getBalance();
console.log(`Số dư: ${balanceETH} ETH`);
```

### 4. Lấy Trạng thái Blockchain

```bash
curl http://localhost:5000/api/blockchain/status
```

Response:
```json
{
    "success": true,
    "blockchain": {
        "connected": true,
        "network": "sepolia",
        "latest_block": 4892401,
        "gas_price": 25.5,
        "account": "0x123...",
        "balance_eth": 1.234,
        "contract_address": "0x456...",
        "pending_violations": 0
    }
}
```

### 5. Đồng Bộ Vi Phạm Chưa Ghi

Khi blockchain không khả dụng, vi phạm sẽ được lưu cục bộ. Sau đó đồng bộ:

```bash
curl -X POST http://localhost:5000/api/blockchain/sync-violations
```

---

## 📡 API Reference

### Blockchain Endpoints

#### 1. Lấy Trạng Thái Blockchain
```
GET /api/blockchain/status

Response:
{
    "success": true,
    "blockchain": {
        "connected": true,
        "network": "sepolia",
        "latest_block": 4892401,
        "gas_price": 25.5,
        "account": "0x123...",
        "balance_eth": 1.234,
        "contract_address": "0x456...",
        "pending_violations": 0
    }
}
```

#### 2. Kết Nối Blockchain
```
POST /api/blockchain/connect

Body:
{
    "private_key": "0x...",
    "contract_address": "0x...",
    "network": "sepolia"
}

Response:
{
    "success": true,
    "message": "Kết nối blockchain sepolia thành công",
    "account": "0x123...",
    "balance": 1.234
}
```

#### 3. Ghi Vi Phạm
```
POST /api/blockchain/record-violation

Body:
{
    "vehicle_id": "29A123456",
    "violation_type": "red_light",
    "severity": "severe",
    "location": "12.9716,77.5946",
    "image_hash": "QmXyZ..."
}

Response:
{
    "success": true,
    "message": "Vi phạm đã được ghi lên blockchain",
    "transaction": {
        "tx_hash": "0x...",
        "violation_hash": "abc123...",
        "block_number": 4892401,
        "vehicle_id": "29A123456",
        "violation_type": "red_light",
        "timestamp": 1686502000,
        "status": "confirmed"
    }
}
```

#### 4. Lấy Vi Phạm
```
GET /api/blockchain/violation/{violation_hash}

Response:
{
    "success": true,
    "violation": {
        "vehicle_id": "29A123456",
        "timestamp": 1686502000,
        "violation_type": "red_light",
        "severity": "severe",
        "recorded_by": "0x123..."
    }
}
```

#### 5. Lấy Tất Cả Vi Phạm của Xe
```
GET /api/blockchain/violations/{vehicle_id}

Response:
{
    "success": true,
    "vehicle_id": "29A123456",
    "violations": [
        {
            "vehicle_id": "29A123456",
            "timestamp": 1686502000,
            "violation_type": "red_light",
            "severity": "severe",
            "recorded_by": "0x123..."
        },
        ...
    ],
    "total": 5
}
```

#### 6. Lấy Số Dư
```
GET /api/blockchain/account-balance

Response:
{
    "success": true,
    "balance_eth": 1.234,
    "account": "0x123..."
}
```

#### 7. Đồng Bộ Vi Phạm
```
POST /api/blockchain/sync-violations

Response:
{
    "success": true,
    "message": "Đã đồng bộ 3 vi phạm lên blockchain",
    "synced_count": 3,
    "pending_count": 0
}
```

### MetaMask Endpoints

#### 1. Kết Nối MetaMask
```
POST /api/metamask/connect

Body:
{
    "account": "0x123...",
    "network_id": "11155111"
}

Response:
{
    "success": true,
    "account": "0x123...",
    "network_id": "11155111",
    "network_name": "Sepolia Testnet",
    "connected_at": "2024-06-03T10:30:00",
    "contract_address": "0x456..."
}
```

#### 2. Ngắt Kết Nối MetaMask
```
POST /api/metamask/disconnect

Response:
{
    "success": true,
    "message": "Đã ngắt kết nối MetaMask"
}
```

#### 3. Lấy Trạng Thái MetaMask
```
GET /api/metamask/status

Response:
{
    "success": true,
    "metamask": {
        "connected": true,
        "account": "0x123...",
        "network_id": "11155111",
        "connection_timestamp": "2024-06-03T10:30:00",
        "contract_address": "0x456...",
        "blockchain_status": {...}
    }
}
```

---

## 🧪 Testing

### 1. Test Kết Nối Blockchain

```python
# test_blockchain.py
from blockchain import blockchain_manager
import os
from dotenv import load_dotenv

load_dotenv()

# Kiểm tra kết nối
status = blockchain_manager.get_network_status()
print("Network Status:", status)

# Kết nối ví
private_key = os.getenv('PRIVATE_KEY')
contract_addr = os.getenv('VIOLATION_CONTRACT_ADDRESS')

if blockchain_manager.connect_wallet(private_key, contract_addr):
    print("✓ Ví đã kết nối")
    
    # Lấy số dư
    balance = blockchain_manager.get_account_balance()
    print(f"Số dư: {balance} ETH")
else:
    print("✗ Lỗi kết nối ví")
```

### 2. Test Ghi Vi Phạm

```python
# Ghi test violation
result = blockchain_manager.record_violation(
    vehicle_id="TEST_CAR_001",
    violation_type="red_light",
    severity="moderate",
    location="0,0",
    image_hash="test_hash_123"
)

if result:
    print(f"✓ Transaction: {result['tx_hash']}")
else:
    print("✗ Lỗi ghi vi phạm")
```

---

## ⚠️ Troubleshooting

### 1. "Connection failed"
- Kiểm tra BLOCKCHAIN_NETWORK trong .env
- Kiểm tra internet connection
- Kiểm tra RPC URL

### 2. "Invalid private key"
- Format private key phải là hex string bắt đầu với `0x`
- Kiểm tra độ dài (66 characters)

### 3. "MetaMask not detected"
- Kiểm tra MetaMask extension đã cài
- Kiểm tra browser có hỗ trợ window.ethereum

### 4. "Insufficient gas"
- Lấy thêm testnet ETH từ faucet
- Kiểm tra gas price

### 5. "Contract not found"
- Kiểm tra VIOLATION_CONTRACT_ADDRESS trong .env
- Kiểm tra address có hợp lệ (checksum address)
- Kiểm tra address có đúng network

---

## 📚 Tài Liệu Thêm

- **Web3.py**: https://web3py.readthedocs.io/
- **MetaMask Docs**: https://docs.metamask.io/
- **Sepolia Testnet**: https://sepolia.etherscan.io/
- **Mumbai Testnet**: https://mumbai.polygonscan.com/
- **Solidity Docs**: https://docs.soliditylang.org/

---

## 🎯 Next Steps

1. ✅ Deploy smart contract
2. ✅ Cập nhật `.env` với contract address
3. ✅ Test blockchain connection
4. ✅ Tích hợp với web interface
5. ✅ Test MetaMask integration
6. ✅ Xây dựng violation recording workflow

---

**Hỗ trợ**: Nếu gặp vấn đề, kiểm tra console logs hoặc liên hệ support.
