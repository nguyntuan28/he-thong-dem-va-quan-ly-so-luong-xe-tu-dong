/**
 * MetaMask Integration Script
 * Xử lý kết nối MetaMask và blockchain interactions từ web interface
 */

class MetaMaskIntegration {
    constructor() {
        this.provider = null;
        this.account = null;
        this.networkId = null;
        this.isConnected = false;
        this.contractAddress = null;
        
        this.initializeListeners();
    }
    
    /**
     * Khởi tạo listeners cho MetaMask events
     */
    initializeListeners() {
        if (window.ethereum) {
            // Khi tài khoản thay đổi
            window.ethereum.on('accountsChanged', (accounts) => {
                if (accounts.length > 0) {
                    this.onAccountChanged(accounts[0]);
                } else {
                    this.onDisconnected();
                }
            });
            
            // Khi mạng thay đổi
            window.ethereum.on('chainChanged', (chainId) => {
                this.onNetworkChanged(chainId);
            });
            
            // Khi disconnect
            window.ethereum.on('disconnect', () => {
                this.onDisconnected();
            });
        }
    }
    
    /**
     * Kiểm tra xem MetaMask có được cài đặt không
     */
    isMetaMaskInstalled() {
        return !!window.ethereum && !!window.ethereum.isMetaMask;
    }
    
    /**
     * Kết nối với MetaMask
     */
    async connect() {
        if (!this.isMetaMaskInstalled()) {
            alert('MetaMask chưa được cài đặt! Hãy cài đặt MetaMask từ https://metamask.io');
            return false;
        }
        
        try {
            // Yêu cầu kết nối
            const accounts = await window.ethereum.request({
                method: 'eth_requestAccounts'
            });
            
            this.account = accounts[0];
            this.provider = window.ethereum;
            
            // Lấy network ID
            const networkId = await window.ethereum.request({
                method: 'net_version'
            });
            
            this.networkId = networkId;
            
            // Gửi thông tin kết nối lên server
            const response = await fetch('/api/metamask/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    account: this.account,
                    network_id: networkId
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.isConnected = true;
                this.contractAddress = result.contract_address;
                console.log('✓ MetaMask kết nối thành công:', this.account);
                this.updateUI();
                return true;
            } else {
                console.error('✗ Lỗi kết nối:', result.error);
                return false;
            }
        } catch (error) {
            console.error('✗ Lỗi MetaMask:', error);
            return false;
        }
    }
    
    /**
     * Ngắt kết nối MetaMask
     */
    async disconnect() {
        try {
            const response = await fetch('/api/metamask/disconnect', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.isConnected = false;
                this.account = null;
                this.provider = null;
                console.log('✓ Đã ngắt kết nối MetaMask');
                this.updateUI();
                return true;
            }
            return false;
        } catch (error) {
            console.error('✗ Lỗi ngắt kết nối:', error);
            return false;
        }
    }
    
    /**
     * Xử lý khi tài khoản thay đổi
     */
    async onAccountChanged(newAccount) {
        console.log('📝 Tài khoản thay đổi:', newAccount);
        this.account = newAccount;
        this.updateUI();
    }
    
    /**
     * Xử lý khi mạng thay đổi
     */
    async onNetworkChanged(newChainId) {
        console.log('🌐 Mạng thay đổi:', newChainId);
        this.networkId = parseInt(newChainId, 16).toString();
        
        // Gửi notification lên server
        try {
            await fetch('/api/metamask/network-changed', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    network_id: this.networkId
                })
            });
        } catch (error) {
            console.error('✗ Lỗi cập nhật mạng:', error);
        }
        
        this.updateUI();
    }
    
    /**
     * Xử lý khi disconnect
     */
    async onDisconnected() {
        console.log('🔌 MetaMask đã ngắt kết nối');
        this.isConnected = false;
        this.account = null;
        this.updateUI();
    }
    
    /**
     * Ký một tin nhắn
     */
    async signMessage(message) {
        if (!this.isConnected || !this.account) {
            alert('Vui lòng kết nối MetaMask trước');
            return null;
        }
        
        try {
            const signature = await window.ethereum.request({
                method: 'personal_sign',
                params: [message, this.account]
            });
            
            console.log('✓ Ký tin nhắn thành công');
            return signature;
        } catch (error) {
            console.error('✗ Lỗi ký tin nhắn:', error);
            return null;
        }
    }
    
    /**
     * Gửi transaction ghi vi phạm lên blockchain
     */
    async recordViolation(vehicleId, violationType, severity, location, imageHash) {
        if (!this.isConnected || !this.account) {
            alert('Vui lòng kết nối MetaMask trước');
            return false;
        }
        
        try {
            // Gọi API Flask để ghi vi phạm
            const response = await fetch('/api/blockchain/record-violation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    vehicle_id: vehicleId,
                    violation_type: violationType,
                    severity: severity,
                    location: location,
                    image_hash: imageHash
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('✓ Vi phạm đã ghi lên blockchain:', result.transaction);
                return result.transaction;
            } else {
                console.error('✗ Lỗi ghi vi phạm:', result.error);
                return false;
            }
        } catch (error) {
            console.error('✗ Lỗi ghi vi phạm:', error);
            return false;
        }
    }
    
    /**
     * Lấy tất cả vi phạm của một xe từ blockchain
     */
    async getVehicleViolations(vehicleId) {
        try {
            const response = await fetch(`/api/blockchain/violations/${vehicleId}`);
            const result = await response.json();
            
            if (result.success) {
                return result.violations;
            } else {
                console.error('✗ Lỗi lấy vi phạm:', result.error);
                return null;
            }
        } catch (error) {
            console.error('✗ Lỗi lấy vi phạm:', error);
            return null;
        }
    }
    
    /**
     * Lấy số dư tài khoản (ETH)
     */
    async getBalance() {
        try {
            const response = await fetch('/api/blockchain/account-balance');
            const result = await response.json();
            
            if (result.success) {
                return result.balance_eth;
            }
            return null;
        } catch (error) {
            console.error('✗ Lỗi lấy số dư:', error);
            return null;
        }
    }
    
    /**
     * Lấy trạng thái blockchain
     */
    async getBlockchainStatus() {
        try {
            const response = await fetch('/api/blockchain/status');
            const result = await response.json();
            return result.blockchain;
        } catch (error) {
            console.error('✗ Lỗi lấy trạng thái:', error);
            return null;
        }
    }
    
    /**
     * Cập nhật UI với thông tin kết nối
     */
    updateUI() {
        // Cập nhật button kết nối
        const connectBtn = document.getElementById('metamask-connect-btn');
        const statusDiv = document.getElementById('metamask-status');
        
        if (connectBtn) {
            if (this.isConnected) {
                connectBtn.textContent = `Ngắt kết nối (${this.account?.substring(0, 6)}...)`;
                connectBtn.className = 'btn btn-danger';
                connectBtn.onclick = () => this.disconnect();
            } else {
                connectBtn.textContent = 'Kết nối MetaMask';
                connectBtn.className = 'btn btn-primary';
                connectBtn.onclick = () => this.connect();
            }
        }
        
        // Cập nhật trạng thái
        if (statusDiv) {
            if (this.isConnected) {
                statusDiv.innerHTML = `
                    <div class="alert alert-success">
                        ✓ Đã kết nối MetaMask<br>
                        Tài khoản: <strong>${this.account}</strong><br>
                        Mạng ID: <strong>${this.networkId}</strong>
                    </div>
                `;
            } else {
                statusDiv.innerHTML = `
                    <div class="alert alert-warning">
                        ⚠️ Chưa kết nối MetaMask
                    </div>
                `;
            }
        }
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('metamaskStatusChanged', {
            detail: {
                isConnected: this.isConnected,
                account: this.account,
                networkId: this.networkId
            }
        }));
    }
    
    /**
     * Lấy network name từ network ID
     */
    getNetworkName() {
        const networks = {
            '1': 'Ethereum Mainnet',
            '11155111': 'Sepolia Testnet',
            '137': 'Polygon Mainnet',
            '80001': 'Mumbai Testnet'
        };
        return networks[this.networkId] || 'Unknown Network';
    }
}

// Khởi tạo global instance
const metamask = new MetaMaskIntegration();

// Chạy khi DOM ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔌 MetaMask Integration loaded');
    metamask.updateUI();
});
