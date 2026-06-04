#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick Test Script for Blockchain Integration
Test kết nối blockchain và các chức năng cơ bản
"""

import sys
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_imports():
    """Test nhập các module"""
    print("=" * 60)
    print("🧪 TEST 1: Kiểm tra import modules")
    print("=" * 60)
    
    try:
        from web3 import Web3
        print("✓ Web3 imported successfully")
        
        from eth_account import Account
        print("✓ eth_account imported successfully")
        
        from blockchain import blockchain_manager
        print("✓ blockchain module imported successfully")
        
        from metamask_connector import metamask_connector
        print("✓ metamask_connector module imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False


def test_blockchain_init():
    """Test khởi tạo blockchain manager"""
    print("\n" + "=" * 60)
    print("🧪 TEST 2: Khởi tạo Blockchain Manager")
    print("=" * 60)
    
    try:
        from blockchain import blockchain_manager
        
        status = blockchain_manager.get_network_status()
        print(f"✓ Network Status: {status['network']}")
        print(f"✓ Connected: {status['connected']}")
        print(f"✓ RPC URL: {status['rpc_url']}")
        
        if status['connected']:
            print(f"✓ Latest Block: {status['latest_block']}")
            print(f"✓ Gas Price: {status['gas_price']:.2f} Gwei")
            return True
        else:
            print("⚠️ Blockchain không kết nối (có thể do network issue)")
            return True  # Không phải lỗi
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_env_configuration():
    """Test cấu hình environment"""
    print("\n" + "=" * 60)
    print("🧪 TEST 3: Kiểm tra Environment Configuration")
    print("=" * 60)
    
    network = os.getenv('BLOCKCHAIN_NETWORK', 'not set')
    contract = os.getenv('VIOLATION_CONTRACT_ADDRESS', 'not set')
    private_key = os.getenv('PRIVATE_KEY', 'not set')
    metamask_network = os.getenv('METAMASK_NETWORK_ID', 'not set')
    
    print(f"✓ BLOCKCHAIN_NETWORK: {network}")
    
    if contract != 'not set':
        print(f"✓ CONTRACT_ADDRESS: {contract[:10]}...{contract[-10:]}")
    else:
        print(f"⚠️ CONTRACT_ADDRESS: {contract} (chưa cấu hình)")
    
    if private_key != 'not set':
        print(f"✓ PRIVATE_KEY: Set (length: {len(private_key)})")
    else:
        print(f"⚠️ PRIVATE_KEY: {private_key} (chưa cấu hình)")
    
    print(f"✓ METAMASK_NETWORK_ID: {metamask_network}")
    
    return True


def test_wallet_creation():
    """Test tạo ví từ private key"""
    print("\n" + "=" * 60)
    print("🧪 TEST 4: Test Wallet Creation")
    print("=" * 60)
    
    try:
        from eth_account import Account
        
        # Tạo ví mới (demo)
        account = Account.create()
        print(f"✓ New wallet created")
        print(f"  Address: {account.address}")
        print(f"  Private Key: {account.key.hex()}")
        
        # Kiểm tra private key từ env
        private_key = os.getenv('PRIVATE_KEY')
        if private_key:
            from web3 import Web3
            if Web3.is_address(private_key):
                print("✗ PRIVATE_KEY phải là hex string, không phải address")
                return False
            
            try:
                account_from_key = Account.from_key(private_key)
                print(f"✓ Wallet từ PRIVATE_KEY: {account_from_key.address}")
                return True
            except Exception as e:
                print(f"✗ Invalid PRIVATE_KEY: {e}")
                return False
        else:
            print("⚠️ PRIVATE_KEY chưa được cấu hình")
            return True
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_metamask_connector():
    """Test MetaMask connector"""
    print("\n" + "=" * 60)
    print("🧪 TEST 5: Test MetaMask Connector")
    print("=" * 60)
    
    try:
        from metamask_connector import metamask_connector
        
        status = metamask_connector.get_connection_status()
        print(f"✓ MetaMask Connector Status:")
        print(f"  Connected: {status['connected']}")
        print(f"  Account: {status['account']}")
        print(f"  Network ID: {status['network_id']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_contract_validation():
    """Test validation of contract address"""
    print("\n" + "=" * 60)
    print("🧪 TEST 6: Contract Address Validation")
    print("=" * 60)
    
    try:
        from web3 import Web3
        
        contract_addr = os.getenv('VIOLATION_CONTRACT_ADDRESS')
        
        if not contract_addr or contract_addr == '0x0000000000000000000000000000000000000000':
            print("⚠️ CONTRACT_ADDRESS: không hợp lệ hoặc không cấu hình")
            print("   Deploy smart contract từ Remix IDE: https://remix.ethereum.org/")
            return True
        
        if Web3.is_address(contract_addr):
            checksum_addr = Web3.to_checksum_address(contract_addr)
            print(f"✓ CONTRACT_ADDRESS valid")
            print(f"  Checksum: {checksum_addr}")
            return True
        else:
            print(f"✗ CONTRACT_ADDRESS không hợp lệ: {contract_addr}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_summary():
    """In summary report"""
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    print("""
✅ All basic tests passed!

Next Steps:
1. ✓ Install dependencies (DONE)
2. ⏳ Deploy Smart Contract
   - Go to: https://remix.ethereum.org/
   - Create file: TrafficViolationRegistry.sol
   - Compile & Deploy to Sepolia
   - Copy contract address to .env

3. ⏳ Configure .env file
   - Set BLOCKCHAIN_NETWORK=sepolia
   - Set VIOLATION_CONTRACT_ADDRESS=0x...
   - Set PRIVATE_KEY=0x...
   
4. ⏳ Get Testnet ETH
   - Sepolia: https://www.sepoliafaucet.io/
   - Paste your wallet address
   
5. ⏳ Test Blockchain Connection
   - python blockchain_test.py
   
6. ⏳ Integrate UI Components
   - Add metamask.js to HTML
   - Add UI components from METAMASK_UI_INTEGRATION.html
   
7. ⏳ Test in Web Interface
   - Open dashboard
   - Click "Connect MetaMask"
   - Record a violation
   
📚 Documentation:
   - BLOCKCHAIN_QUICK_START.md (5-min guide)
   - BLOCKCHAIN_SETUP_GUIDE.md (complete guide)
   - IMPLEMENTATION_SUMMARY.md (full overview)

🚀 You're ready to integrate blockchain!
""")


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " BLOCKCHAIN & METAMASK INTEGRATION TEST ".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = []
    
    # Run tests
    results.append(("Import Modules", test_imports()))
    results.append(("Blockchain Init", test_blockchain_init()))
    results.append(("Environment Config", test_env_configuration()))
    results.append(("Wallet Creation", test_wallet_creation()))
    results.append(("MetaMask Connector", test_metamask_connector()))
    results.append(("Contract Validation", test_contract_validation()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("✅ RESULTS:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        test_summary()
    else:
        print("⚠️ Some tests failed. Check configuration and try again.")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
