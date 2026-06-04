// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * Traffic Violation Registry Smart Contract
 * Lưu trữ và quản lý các vi phạm giao thông trên blockchain
 */

contract TrafficViolationRegistry {
    
    // Struct để lưu thông tin vi phạm
    struct Violation {
        string vehicleId;
        uint256 timestamp;
        string violationType;        // "red_light", "speeding", "parking_violation"
        string severity;             // "severe", "moderate", "minor"
        address recordedBy;          // Địa chỉ của người ghi nhận
        string location;
        string imageHash;            // IPFS hash của ảnh
        bool confirmed;
    }
    
    // Admin account
    address public admin;
    
    // Mapping từ violation hash sang Violation struct
    mapping(string => Violation) public violations;
    
    // Mapping từ vehicle ID sang danh sách violation hashes
    mapping(string => string[]) public vehicleViolations;
    
    // Array toàn bộ violation hashes
    string[] public allViolationHashes;
    
    // Events
    event ViolationRecorded(
        string indexed violationHash,
        string vehicleId,
        string violationType,
        uint256 timestamp
    );
    
    event ViolationConfirmed(
        string indexed violationHash,
        address confirmedBy
    );
    
    event ViolationRemoved(
        string indexed violationHash
    );
    
    // Modifiers
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }
    
    /**
     * Constructor - khởi tạo contract
     */
    constructor() {
        admin = msg.sender;
    }
    
    /**
     * Ghi lại một vi phạm
     */
    function recordViolation(
        string memory violationHash,
        string memory vehicleId,
        uint256 timestamp,
        string memory violationType,
        string memory severity,
        string memory location,
        string memory imageHash
    ) public onlyAdmin {
        require(
            bytes(violationHash).length > 0,
            "Violation hash cannot be empty"
        );
        require(
            bytes(vehicleId).length > 0,
            "Vehicle ID cannot be empty"
        );
        
        // Kiểm tra violation chưa tồn tại
        require(
            bytes(violations[violationHash].vehicleId).length == 0,
            "Violation already exists"
        );
        
        // Lưu vi phạm
        violations[violationHash] = Violation(
            vehicleId,
            timestamp,
            violationType,
            severity,
            msg.sender,
            location,
            imageHash,
            false
        );
        
        // Thêm vào danh sách xe
        vehicleViolations[vehicleId].push(violationHash);
        
        // Thêm vào danh sách toàn bộ
        allViolationHashes.push(violationHash);
        
        // Phát event
        emit ViolationRecorded(
            violationHash,
            vehicleId,
            violationType,
            timestamp
        );
    }
    
    /**
     * Lấy thông tin chi tiết một vi phạm
     */
    function getViolation(string memory violationHash)
        public
        view
        returns (
            string memory vehicleId,
            uint256 timestamp,
            string memory violationType,
            string memory severity,
            address recordedBy
        )
    {
        Violation memory v = violations[violationHash];
        require(
            bytes(v.vehicleId).length > 0,
            "Violation not found"
        );
        
        return (
            v.vehicleId,
            v.timestamp,
            v.violationType,
            v.severity,
            v.recordedBy
        );
    }
    
    /**
     * Lấy tất cả vi phạm của một xe
     */
    function getViolationsByVehicle(string memory vehicleId)
        public
        view
        returns (string[] memory)
    {
        return vehicleViolations[vehicleId];
    }
    
    /**
     * Lấy số vi phạm của một xe
     */
    function getViolationCount(string memory vehicleId)
        public
        view
        returns (uint256)
    {
        return vehicleViolations[vehicleId].length;
    }
    
    /**
     * Lấy thông tin chi tiết vi phạm bao gồm location và imageHash
     */
    function getFullViolationDetails(string memory violationHash)
        public
        view
        returns (
            string memory vehicleId,
            uint256 timestamp,
            string memory violationType,
            string memory severity,
            address recordedBy,
            string memory location,
            string memory imageHash,
            bool confirmed
        )
    {
        Violation memory v = violations[violationHash];
        require(
            bytes(v.vehicleId).length > 0,
            "Violation not found"
        );
        
        return (
            v.vehicleId,
            v.timestamp,
            v.violationType,
            v.severity,
            v.recordedBy,
            v.location,
            v.imageHash,
            v.confirmed
        );
    }
    
    /**
     * Xác nhận vi phạm (chỉ admin)
     */
    function confirmViolation(string memory violationHash)
        public
        onlyAdmin
    {
        require(
            bytes(violations[violationHash].vehicleId).length > 0,
            "Violation not found"
        );
        
        violations[violationHash].confirmed = true;
        
        emit ViolationConfirmed(violationHash, msg.sender);
    }
    
    /**
     * Xóa vi phạm (chỉ admin)
     */
    function removeViolation(string memory violationHash)
        public
        onlyAdmin
    {
        require(
            bytes(violations[violationHash].vehicleId).length > 0,
            "Violation not found"
        );
        
        string memory vehicleId = violations[violationHash].vehicleId;
        
        // Xóa khỏi mapping
        delete violations[violationHash];
        
        emit ViolationRemoved(violationHash);
    }
    
    /**
     * Lấy tổng số vi phạm
     */
    function getTotalViolations() public view returns (uint256) {
        return allViolationHashes.length;
    }
    
    /**
     * Lấy danh sách vi phạm với phân trang
     */
    function getViolationsPaginated(uint256 offset, uint256 limit)
        public
        view
        returns (string[] memory)
    {
        uint256 totalCount = allViolationHashes.length;
        
        require(offset < totalCount, "Offset out of bounds");
        
        uint256 endIndex = offset + limit;
        if (endIndex > totalCount) {
            endIndex = totalCount;
        }
        
        string[] memory result = new string[](endIndex - offset);
        
        for (uint256 i = offset; i < endIndex; i++) {
            result[i - offset] = allViolationHashes[i];
        }
        
        return result;
    }
    
    /**
     * Đổi admin (chỉ admin hiện tại)
     */
    function changeAdmin(address newAdmin) public onlyAdmin {
        require(newAdmin != address(0), "Invalid admin address");
        admin = newAdmin;
    }
    
    /**
     * Lấy thông tin admin
     */
    function getAdmin() public view returns (address) {
        return admin;
    }
}
