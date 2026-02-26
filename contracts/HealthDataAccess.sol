// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title HealthDataAccess
 * @dev 健康数据存储与访问控制合约
 * 实现数据的去中心化存储、加密和访问权限管理
 */
contract HealthDataAccess {
    
    struct HealthRecord {
        bytes32 dataHash;        // 数据哈希值
        bytes32 encryptedData;   // 加密后的数据
        uint256 timestamp;       // 记录时间
        address owner;          // 数据所有者
        bool isActive;          // 数据是否有效
        string dataType;        // 数据类型（血压、心率等）
    }
    
    struct AccessPermission {
        address requester;      // 请求者地址
        bytes32 dataId;        // 数据ID
        uint256 grantedAt;     // 授权时间
        uint256 expiresAt;     // 过期时间
        bool canRead;          // 是否可读
        bool canWrite;         // 是否可写
        address granter;       // 授权者
    }
    
    // 数据存储映射
    mapping(bytes32 => HealthRecord) public healthRecords;
    
    // 访问权限映射
    mapping(address => mapping(bytes32 => AccessPermission)) public permissions;
    
    // 用户数据列表
    mapping(address => bytes32[]) public userRecords;
    
    // 数据授权事件
    event DataStored(
        address indexed owner,
        bytes32 indexed dataId,
        string dataType,
        uint256 timestamp
    );
    
    event AccessGranted(
        address indexed granter,
        address indexed requester,
        bytes32 indexed dataId,
        uint256 expiresAt
    );
    
    event AccessRevoked(
        address indexed granter,
        address indexed requester,
        bytes32 indexed dataId
    );
    
    event DataUpdated(
        address indexed owner,
        bytes32 indexed dataId,
        uint256 timestamp
    );
    
    // 修饰符：只有数据所有者可以操作
    modifier onlyDataOwner(bytes32 dataId) {
        require(healthRecords[dataId].owner == msg.sender, "Not data owner");
        _;
    }
    
    // 修饰符：检查访问权限
    modifier hasReadPermission(bytes32 dataId) {
        require(
            healthRecords[dataId].owner == msg.sender || 
            (permissions[msg.sender][dataId].canRead && 
             block.timestamp < permissions[msg.sender][dataId].expiresAt),
            "No read permission"
        );
        _;
    }
    
    // 修饰符：检查写入权限
    modifier hasWritePermission(bytes32 dataId) {
        require(
            healthRecords[dataId].owner == msg.sender || 
            (permissions[msg.sender][dataId].canWrite && 
             block.timestamp < permissions[msg.sender][dataId].expiresAt),
            "No write permission"
        );
        _;
    }
    
    /**
     * @dev 存储健康数据
     * @param dataHash 数据哈希值
     * @param encryptedData 加密后的数据
     * @param dataType 数据类型
     */
    function storeHealthData(
        bytes32 dataHash,
        bytes32 encryptedData,
        string memory dataType
    ) public returns (bytes32) {
        // 生成数据ID
        bytes32 dataId = keccak256(abi.encodePacked(
            msg.sender,
            dataHash,
            block.timestamp
        ));
        
        // 检查数据是否已存在
        require(healthRecords[dataId].owner == address(0), "Data already exists");
        
        // 存储数据
        healthRecords[dataId] = HealthRecord({
            dataHash: dataHash,
            encryptedData: encryptedData,
            timestamp: block.timestamp,
            owner: msg.sender,
            isActive: true,
            dataType: dataType
        });
        
        // 添加到用户数据列表
        userRecords[msg.sender].push(dataId);
        
        emit DataStored(msg.sender, dataId, dataType, block.timestamp);
        
        return dataId;
    }
    
    /**
     * @dev 获取健康数据
     * @param dataId 数据ID
     */
    function getHealthData(bytes32 dataId) 
        public 
        view 
        hasReadPermission(dataId) 
        returns (
            bytes32 dataHash,
            bytes32 encryptedData,
            uint256 timestamp,
            address owner,
            string memory dataType
        ) 
    {
        HealthRecord storage record = healthRecords[dataId];
        require(record.isActive, "Data not active");
        
        return (
            record.dataHash,
            record.encryptedData,
            record.timestamp,
            record.owner,
            record.dataType
        );
    }
    
    /**
     * @dev 更新健康数据
     * @param dataId 数据ID
     * @param newDataHash 新的数据哈希
     * @param newEncryptedData 新的加密数据
     */
    function updateHealthData(
        bytes32 dataId,
        bytes32 newDataHash,
        bytes32 newEncryptedData
    ) public hasWritePermission(dataId) {
        HealthRecord storage record = healthRecords[dataId];
        require(record.isActive, "Data not active");
        
        record.dataHash = newDataHash;
        record.encryptedData = newEncryptedData;
        record.timestamp = block.timestamp;
        
        emit DataUpdated(record.owner, dataId, block.timestamp);
    }
    
    /**
     * @dev 授权访问权限
     * @param requester 请求者地址
     * @param dataId 数据ID
     * @param canRead 是否可读
     * @param canWrite 是否可写
     * @param duration 授权时长（秒）
     */
    function grantAccess(
        address requester,
        bytes32 dataId,
        bool canRead,
        bool canWrite,
        uint256 duration
    ) public onlyDataOwner(dataId) {
        require(requester != address(0), "Invalid requester");
        require(duration > 0, "Invalid duration");
        
        uint256 expiresAt = block.timestamp + duration;
        
        permissions[requester][dataId] = AccessPermission({
            requester: requester,
            dataId: dataId,
            grantedAt: block.timestamp,
            expiresAt: expiresAt,
            canRead: canRead,
            canWrite: canWrite,
            granter: msg.sender
        });
        
        emit AccessGranted(msg.sender, requester, dataId, expiresAt);
    }
    
    /**
     * @dev 撤销访问权限
     * @param requester 请求者地址
     * @param dataId 数据ID
     */
    function revokeAccess(address requester, bytes32 dataId) 
        public 
        onlyDataOwner(dataId) 
    {
        delete permissions[requester][dataId];
        emit AccessRevoked(msg.sender, requester, dataId);
    }
    
    /**
     * @dev 获取用户的所有数据ID
     * @param user 用户地址
     */
    function getUserDataIds(address user) public view returns (bytes32[] memory) {
        return userRecords[user];
    }
    
    /**
     * @dev 获取数据数量
     * @param user 用户地址
     */
    function getUserDataCount(address user) public view returns (uint256) {
        return userRecords[user].length;
    }
    
    /**
     * @dev 检查权限状态
     * @param requester 请求者地址
     * @param dataId 数据ID
     */
    function checkPermission(address requester, bytes32 dataId) 
        public 
        view 
        returns (
            bool hasPermission,
            bool canRead,
            bool canWrite,
            uint256 expiresAt
        ) 
    {
        AccessPermission storage permission = permissions[requester][dataId];
        
        if (block.timestamp >= permission.expiresAt) {
            return (false, false, false, 0);
        }
        
        return (
            true,
            permission.canRead,
            permission.canWrite,
            permission.expiresAt
        );
    }
    
    /**
     * @dev 删除数据（仅所有者）
     * @param dataId 数据ID
     */
    function deleteData(bytes32 dataId) public onlyDataOwner(dataId) {
        HealthRecord storage record = healthRecords[dataId];
        require(record.isActive, "Data already inactive");
        
        record.isActive = false;
        
        // 从用户数据列表中移除
        bytes32[] storage dataList = userRecords[msg.sender];
        for (uint256 i = 0; i < dataList.length; i++) {
            if (dataList[i] == dataId) {
                dataList[i] = dataList[dataList.length - 1];
                dataList.pop();
                break;
            }
        }
    }
    
    /**
     * @dev 批量授权
     * @param requester 请求者地址
     * @param dataIds 数据ID数组
     * @param canRead 是否可读
     * @param canWrite 是否可写
     * @param duration 授权时长
     */
    function batchGrantAccess(
        address requester,
        bytes32[] memory dataIds,
        bool canRead,
        bool canWrite,
        uint256 duration
    ) public {
        for (uint256 i = 0; i < dataIds.length; i++) {
            if (healthRecords[dataIds[i]].owner == msg.sender) {
                grantAccess(requester, dataIds[i], canRead, canWrite, duration);
            }
        }
    }
    
    /**
     * @dev 获取合约信息
     */
    function getContractInfo() public view returns (
        uint256 totalRecords,
        uint256 activeRecords
    ) {
        // 这里简化实现，实际应该维护计数器
        return (0, 0);
    }
}
