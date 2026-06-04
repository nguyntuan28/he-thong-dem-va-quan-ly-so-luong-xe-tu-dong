"""
MetaMask Connector - Tích hợp kết nối ví MetaMask từ web interface
Xử lý yêu cầu kết nối từ JavaScript frontend
"""

import json
from typing import Dict, Optional
from datetime import datetime
from blockchain import blockchain_manager
import os

class MetaMaskConnector:
    """Quản lý kết nối MetaMask từ web interface"""
    
    def __init__(self):
        self.connected_account = None
        self.network_id = None
        self.contract_address = os.getenv('VIOLATION_CONTRACT_ADDRESS', '')
        self.connection_timestamp = None
        self.session_data = {}
    
    def validate_account(self, account_address: str) -> bool:
        """Kiểm tra địa chỉ ví hợp lệ"""
        from web3 import Web3
        try:
            return Web3.is_address(account_address)
        except:
            return False
    
    def on_account_connected(self, account_address: str, network_id: str) -> Dict:
        """
        Xử lý khi MetaMask kết nối thành công
        
        Args:
            account_address: Địa chỉ ví từ MetaMask
            network_id: ID mạng (1=mainnet, 11155111=sepolia, etc.)
        
        Returns:
            Dữ liệu kết nối
        """
        try:
            if not self.validate_account(account_address):
                return {
                    'success': False,
                    'error': 'Địa chỉ ví không hợp lệ'
                }
            
            self.connected_account = account_address
            self.network_id = network_id
            self.connection_timestamp = datetime.now().isoformat()
            
            # Map network ID
            network_map = {
                '1': 'mainnet',
                '11155111': 'sepolia',
                '137': 'polygon',
                '80001': 'mumbai'
            }
            
            network_name = network_map.get(str(network_id), 'unknown')
            
            print(f"✓ MetaMask kết nối: {account_address[:10]}... on {network_name}")
            
            return {
                'success': True,
                'account': account_address,
                'network_id': network_id,
                'network_name': network_name,
                'connected_at': self.connection_timestamp,
                'contract_address': self.contract_address
            }
            
        except Exception as e:
            print(f"✗ Lỗi kết nối MetaMask: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def on_account_disconnected(self) -> Dict:
        """Xử lý khi MetaMask ngắt kết nối"""
        try:
            self.connected_account = None
            self.network_id = None
            self.connection_timestamp = None
            self.session_data = {}
            
            print("✓ MetaMask ngắt kết nối")
            
            return {
                'success': True,
                'message': 'Đã ngắt kết nối MetaMask'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def on_network_changed(self, new_network_id: str) -> Dict:
        """Xử lý khi người dùng đổi mạng"""
        try:
            old_network = self.network_id
            self.network_id = new_network_id
            
            network_map = {
                '1': 'mainnet',
                '11155111': 'sepolia',
                '137': 'polygon',
                '80001': 'mumbai'
            }
            
            old_name = network_map.get(str(old_network), 'unknown')
            new_name = network_map.get(str(new_network_id), 'unknown')
            
            print(f"✓ Đổi mạng: {old_name} -> {new_name}")
            
            return {
                'success': True,
                'old_network': old_name,
                'new_network': new_name,
                'network_id': new_network_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def sign_message(self, message: str) -> Dict:
        """
        Yêu cầu ký tin nhắn (không dùng private key)
        Điều này sẽ được xử lý ở JavaScript frontend
        
        Args:
            message: Tin nhắn cần ký
        
        Returns:
            Thông tin yêu cầu ký
        """
        return {
            'action': 'sign_message',
            'message': message,
            'account': self.connected_account,
            'timestamp': datetime.now().isoformat()
        }
    
    def request_transaction(
        self,
        to_address: str,
        data: str,
        value: str = "0"
    ) -> Dict:
        """
        Yêu cầu gửi transaction
        
        Args:
            to_address: Địa chỉ smart contract
            data: Encoded function call
            value: Giá trị ETH (nếu có)
        
        Returns:
            Thông tin transaction
        """
        return {
            'action': 'send_transaction',
            'from': self.connected_account,
            'to': to_address,
            'data': data,
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_connection_status(self) -> Dict:
        """Lấy trạng thái kết nối hiện tại"""
        try:
            return {
                'connected': self.connected_account is not None,
                'account': self.connected_account,
                'network_id': self.network_id,
                'connection_timestamp': self.connection_timestamp,
                'contract_address': self.contract_address,
                'blockchain_status': blockchain_manager.get_network_status()
            }
            
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }


# Instance global
metamask_connector = MetaMaskConnector()
