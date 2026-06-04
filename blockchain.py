"""
Blockchain Module - Tích hợp Ethereum/Polygon và MetaMask
Lưu trữ giao dịch vi phạm trên blockchain
"""

import json
import os
from typing import Dict, Optional, Tuple
from datetime import datetime
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import hashlib

load_dotenv()

# ──────────────────────────────────────────────────────────
# Smart Contract ABI (Traffic Violation Registry)
# ──────────────────────────────────────────────────────────

VIOLATION_CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "violationHash", "type": "string"},
            {"internalType": "string", "name": "vehicleId", "type": "string"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "string", "name": "violationType", "type": "string"},
            {"internalType": "string", "name": "severity", "type": "string"},
            {"internalType": "string", "name": "location", "type": "string"},
            {"internalType": "string", "name": "imageHash", "type": "string"}
        ],
        "name": "recordViolation",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "string", "name": "violationHash", "type": "string"}],
        "name": "getViolation",
        "outputs": [
            {"internalType": "string", "name": "vehicleId", "type": "string"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "string", "name": "violationType", "type": "string"},
            {"internalType": "string", "name": "severity", "type": "string"},
            {"internalType": "address", "name": "recordedBy", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "string", "name": "vehicleId", "type": "string"}],
        "name": "getViolationsByVehicle",
        "outputs": [{"internalType": "string[]", "name": "", "type": "string[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "string", "name": "violationHash", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "vehicleId", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "violationType", "type": "string"}
        ],
        "name": "ViolationRecorded",
        "type": "event"
    }
]


class BlockchainManager:
    """Quản lý kết nối blockchain và ghi dữ liệu vi phạm"""
    
    def __init__(self, network: str = "sepolia"):
        """
        Khởi tạo BlockchainManager
        
        Args:
            network: "sepolia", "mainnet", "polygon", "mumbai"
        """
        self.network = network
        self.w3 = None
        self.contract = None
        self.account = None
        self.contract_address = None
        self.violations_local = []  # Backup local violations
        
        self.rpc_urls = {
            "sepolia": "https://sepolia.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161",
            "mainnet": "https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161",
            "polygon": "https://polygon-rpc.com",
            "mumbai": "https://rpc-mumbai.maticvigil.com"
        }
        
        self._initialize()
    
    def _initialize(self):
        """Khởi tạo Web3 connection"""
        try:
            rpc_url = self.rpc_urls.get(self.network)
            if not rpc_url:
                print(f"✗ Network không hỗ trợ: {self.network}")
                return False
            
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not self.w3.is_connected():
                print(f"✗ Không thể kết nối tới {self.network}")
                return False
            
            print(f"✓ Kết nối blockchain {self.network}: {self.w3.provider.endpoint_uri}")
            return True
            
        except Exception as e:
            print(f"✗ Lỗi khởi tạo blockchain: {e}")
            return False
    
    def connect_wallet(self, private_key: str, contract_address: str) -> bool:
        """
        Kết nối ví Ethereum
        
        Args:
            private_key: Private key của ví (từ MetaMask hoặc Infura)
            contract_address: Địa chỉ smart contract
        
        Returns:
            True nếu thành công
        """
        try:
            if not self.w3:
                print("✗ Blockchain chưa được khởi tạo")
                return False
            
            # Tạo account từ private key
            self.account = Account.from_key(private_key)
            
            # Kiểm tra contract address
            if not Web3.is_address(contract_address):
                print(f"✗ Địa chỉ contract không hợp lệ: {contract_address}")
                return False
            
            self.contract_address = Web3.to_checksum_address(contract_address)
            
            # Tạo contract instance
            self.contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=VIOLATION_CONTRACT_ABI
            )
            
            print(f"✓ Kết nối ví thành công: {self.account.address}")
            print(f"✓ Smart Contract: {self.contract_address}")
            return True
            
        except Exception as e:
            print(f"✗ Lỗi kết nối ví: {e}")
            return False
    
    def record_violation(
        self,
        vehicle_id: str,
        violation_type: str,
        severity: str,
        location: str,
        image_hash: str
    ) -> Optional[Dict]:
        """
        Ghi lại vi phạm trên blockchain
        
        Args:
            vehicle_id: ID xe (license plate)
            violation_type: Loại vi phạm (red_light, speeding, etc.)
            severity: Mức độ (severe, moderate, minor)
            location: Vị trí (GPS hoặc address)
            image_hash: Hash của ảnh vi phạm
        
        Returns:
            Transaction receipt hoặc None
        """
        try:
            if not self.contract or not self.account:
                print("✗ Ví hoặc contract chưa được kết nối")
                return self._save_violation_locally(
                    vehicle_id, violation_type, severity, location, image_hash
                )
            
            # Tạo violation hash
            violation_data = f"{vehicle_id}{violation_type}{severity}{location}{image_hash}{datetime.now().isoformat()}"
            violation_hash = hashlib.sha256(violation_data.encode()).hexdigest()
            
            timestamp = int(datetime.now().timestamp())
            
            # Tạo transaction
            tx_data = self.contract.functions.recordViolation(
                violation_hash,
                vehicle_id,
                timestamp,
                violation_type,
                severity,
                location,
                image_hash
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
            })
            
            # Ký transaction
            signed_txn = self.w3.eth.account.sign_transaction(tx_data, self.account.key)
            
            # Gửi transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Chờ receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            print(f"✓ Ghi vi phạm thành công: {tx_hash.hex()}")
            
            return {
                'tx_hash': tx_hash.hex(),
                'violation_hash': violation_hash,
                'block_number': receipt['blockNumber'],
                'vehicle_id': vehicle_id,
                'violation_type': violation_type,
                'timestamp': timestamp,
                'status': 'confirmed'
            }
            
        except Exception as e:
            print(f"✗ Lỗi ghi vi phạm: {e}")
            return self._save_violation_locally(
                vehicle_id, violation_type, severity, location, image_hash
            )
    
    def _save_violation_locally(
        self,
        vehicle_id: str,
        violation_type: str,
        severity: str,
        location: str,
        image_hash: str
    ) -> Dict:
        """Lưu vi phạm cục bộ nếu blockchain không khả dụng"""
        violation = {
            'vehicle_id': vehicle_id,
            'violation_type': violation_type,
            'severity': severity,
            'location': location,
            'image_hash': image_hash,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending_blockchain'
        }
        self.violations_local.append(violation)
        print(f"✓ Lưu vi phạm cục bộ (chưa ghi blockchain)")
        return violation
    
    def get_violation(self, violation_hash: str) -> Optional[Dict]:
        """Lấy thông tin vi phạm từ blockchain"""
        try:
            if not self.contract:
                print("✗ Contract chưa được kết nối")
                return None
            
            result = self.contract.functions.getViolation(violation_hash).call()
            
            return {
                'vehicle_id': result[0],
                'timestamp': result[1],
                'violation_type': result[2],
                'severity': result[3],
                'recorded_by': result[4]
            }
            
        except Exception as e:
            print(f"✗ Lỗi lấy vi phạm: {e}")
            return None
    
    def get_vehicle_violations(self, vehicle_id: str) -> Optional[list]:
        """Lấy tất cả vi phạm của một xe"""
        try:
            if not self.contract:
                print("✗ Contract chưa được kết nối")
                return None
            
            violation_hashes = self.contract.functions.getViolationsByVehicle(
                vehicle_id
            ).call()
            
            violations = []
            for vh in violation_hashes:
                violation = self.get_violation(vh)
                if violation:
                    violations.append(violation)
            
            return violations
            
        except Exception as e:
            print(f"✗ Lỗi lấy danh sách vi phạm: {e}")
            return None
    
    def get_account_balance(self) -> Optional[float]:
        """Lấy số dư tài khoản (ETH)"""
        try:
            if not self.account or not self.w3:
                return None
            
            balance_wei = self.w3.eth.get_balance(self.account.address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            
            return float(balance_eth)
            
        except Exception as e:
            print(f"✗ Lỗi lấy số dư: {e}")
            return None
    
    def sync_pending_violations(self) -> int:
        """Đồng bộ các vi phạm chưa ghi blockchain"""
        try:
            synced_count = 0
            remaining = []
            
            for violation in self.violations_local:
                result = self.record_violation(
                    violation['vehicle_id'],
                    violation['violation_type'],
                    violation['severity'],
                    violation['location'],
                    violation['image_hash']
                )
                
                if result and result.get('tx_hash'):
                    synced_count += 1
                else:
                    remaining.append(violation)
            
            self.violations_local = remaining
            print(f"✓ Đồng bộ {synced_count} vi phạm lên blockchain")
            
            return synced_count
            
        except Exception as e:
            print(f"✗ Lỗi đồng bộ: {e}")
            return 0
    
    def get_network_status(self) -> Dict:
        """Lấy trạng thái mạng blockchain"""
        try:
            if not self.w3:
                return {'connected': False, 'message': 'Blockchain chưa khởi tạo'}
            
            return {
                'connected': self.w3.is_connected(),
                'network': self.network,
                'rpc_url': self.w3.provider.endpoint_uri,
                'latest_block': self.w3.eth.block_number,
                'gas_price': self.w3.from_wei(self.w3.eth.gas_price, 'gwei'),
                'account': self.account.address if self.account else None,
                'balance_eth': self.get_account_balance(),
                'contract_address': self.contract_address,
                'pending_violations': len(self.violations_local)
            }
            
        except Exception as e:
            return {'connected': False, 'error': str(e)}


# Instance global
blockchain_manager = BlockchainManager(network="sepolia")
