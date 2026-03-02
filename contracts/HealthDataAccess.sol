// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/*
 * 新手阅读指南（建议先看这里）：
 * 1) 这个合约不直接保存完整健康数据正文，而是保存：
 *    - dataHash：原始数据的哈希（用于校验是否被篡改）
 *    - encryptedData：加密后的摘要/片段（示例里是 bytes32，真实场景通常会更长）
 * 2) 真正的大文件（PDF、详细文本）一般放链下（数据库/IPFS），链上只放校验信息和权限。
 * 3) 权限模型：
 *    - owner（数据拥有者）天然可读可写
 *    - 其他地址需要 owner 授权，并且授权会过期
 * 4) 事件（event）用于给前端/索引器监听，不是“存数据的主表”。
 */

/**
 * @title HealthDataAccess
 * @dev 健康数据存储与访问控制合约
 * 实现数据的去中心化存储、加密和访问权限管理
 */
contract HealthDataAccess {

    // 数据状态：私密（需要授权）或公开（任何人可读）
    enum DataStatus {
        Private,
        Public
    }

    // 一条健康记录（链上元数据）
    struct HealthRecord {
        bytes32 dataHash;        // 数据哈希值
        bytes32 encryptedData;   // 加密后的数据
        uint256 timestamp;       // 记录时间
        address owner;          // 数据所有者
        bool isActive;          // 数据是否有效
        string dataType;        // 数据类型（血压、心率等）
        DataStatus status;      // 数据状态（私密/公开）
    }
    
    // 对某个 dataId 的授权记录
    struct AccessPermission {
        address requester;      // 请求者地址
        bytes32 dataId;        // 数据ID
        uint256 grantedAt;     // 授权时间
        uint256 expiresAt;     // 过期时间
        bool canRead;          // 是否可读
        bool canWrite;         // 是否可写
        address granter;       // 授权者
    }
    
    // dataId => 健康记录
    mapping(bytes32 => HealthRecord) public healthRecords;
    
    // requester => dataId => 权限
    mapping(address => mapping(bytes32 => AccessPermission)) public permissions;
    
    // owner => 该 owner 拥有的全部 dataId 列表
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

    event DataStatusChanged(
        address indexed owner,
        bytes32 indexed dataId,
        DataStatus oldStatus,
        DataStatus newStatus,
        uint256 timestamp
    );
    
    // 修饰符：只有 dataId 的 owner 才能调用
    modifier onlyDataOwner(bytes32 dataId) {
        require(healthRecords[dataId].owner == msg.sender, "Not data owner");
        _;
    }
    
    // 修饰符：读权限校验（owner 或被授权且未过期）
    modifier hasReadPermission(bytes32 dataId) {
        HealthRecord storage record = healthRecords[dataId];
        require(
            record.owner == msg.sender ||
            (record.status == DataStatus.Public && record.isActive) ||
            (permissions[msg.sender][dataId].canRead && 
             block.timestamp < permissions[msg.sender][dataId].expiresAt),
            "No read permission"
        );
        _;
    }
    
    // 修饰符：写权限校验（owner 或被授权且未过期）
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
        // dataId 由“调用人 + 数据哈希 + 时间”生成，避免冲突
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
            dataType: dataType,
            status: DataStatus.Private
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
        // 注意：这里返回的是链上元数据，不是完整原文
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
        // 被授权写入者也可以更新（不一定是 owner）
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
        HealthRecord storage record = healthRecords[dataId];
        // duration 单位是秒，比如 7 天 = 7 * 24 * 60 * 60
        require(requester != address(0), "Invalid requester");
        require(duration > 0, "Invalid duration");
        require(record.isActive, "Data not active");
        require(record.status == DataStatus.Private, "Public data does not need grant");
        
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
        // delete 会把结构体恢复为默认值（相当于撤销）
        delete permissions[requester][dataId];
        emit AccessRevoked(msg.sender, requester, dataId);
    }

    /**
     * @dev 将数据公开（由所有者执行）
     * @param dataId 数据ID
     */
    function makeDataPublic(bytes32 dataId) public onlyDataOwner(dataId) {
        HealthRecord storage record = healthRecords[dataId];
        require(record.isActive, "Data not active");
        require(record.status == DataStatus.Private, "Already public");

        DataStatus oldStatus = record.status;
        record.status = DataStatus.Public;

        emit DataStatusChanged(
            msg.sender,
            dataId,
            oldStatus,
            DataStatus.Public,
            block.timestamp
        );
    }

    /**
     * @dev 将数据改回私密（由所有者执行）
     * @param dataId 数据ID
     */
    function makeDataPrivate(bytes32 dataId) public onlyDataOwner(dataId) {
        HealthRecord storage record = healthRecords[dataId];
        require(record.isActive, "Data not active");
        require(record.status == DataStatus.Public, "Already private");

        DataStatus oldStatus = record.status;
        record.status = DataStatus.Private;

        emit DataStatusChanged(
            msg.sender,
            dataId,
            oldStatus,
            DataStatus.Private,
            block.timestamp
        );
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
        
        // 已过期就视为无权限
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
     * @dev 检查某地址是否可读该数据（公开数据直接可读）
     * @param requester 请求者地址
     * @param dataId 数据ID
     */
    function checkAccess(address requester, bytes32 dataId) public view returns (bool) {
        HealthRecord storage record = healthRecords[dataId];
        if (!record.isActive) {
            return false;
        }

        if (record.owner == requester) {
            return true;
        }

        if (record.status == DataStatus.Public) {
            return true;
        }

        AccessPermission storage permission = permissions[requester][dataId];
        return permission.canRead && block.timestamp < permission.expiresAt;
    }

    /**
     * @dev 获取数据当前状态（0=Private, 1=Public）
     * @param dataId 数据ID
     */
    function getDataStatus(bytes32 dataId) public view returns (DataStatus) {
        HealthRecord storage record = healthRecords[dataId];
        require(record.owner != address(0), "Data not found");
        return record.status;
    }
    
    /**
     * @dev 删除数据（仅所有者）
     * @param dataId 数据ID
     */
    function deleteData(bytes32 dataId) public onlyDataOwner(dataId) {
        // 这里是“软删除”：只把 isActive 置为 false，并从用户列表移除
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
    function getContractInfo() public pure returns (
        uint256 totalRecords,
        uint256 activeRecords
    ) {
        // 这里简化实现，实际应该维护计数器
        return (0, 0);
    }
}
