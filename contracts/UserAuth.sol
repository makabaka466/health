// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title UserAuth
 * @dev 智能合约用于安全存储用户认证信息
 * 注意：在实际生产环境中，不应该在区块链上存储明文密码
 * 这里仅作为演示，实际应用应该使用密码哈希值
 */
contract UserAuth {
    
    struct User {
        bytes32 usernameHash;     // 用户名的哈希值
        bytes32 passwordHash;     // 密码的哈希值（不是明文）
        uint256 createdAt;        // 创建时间
        bool isActive;           // 账户是否激活
    }
    
    // 映射：用户地址 -> 用户信息
    mapping(address => User) public users;
    
    // 映射：用户名哈希 -> 地址（用于检查用户名是否已存在）
    mapping(bytes32 => address) public usernameToAddress;
    
    // 事件
    event UserRegistered(address indexed userAddress, bytes32 indexed usernameHash, uint256 timestamp);
    event UserLoggedIn(address indexed userAddress, uint256 timestamp);
    event PasswordUpdated(address indexed userAddress, uint256 timestamp);
    event UserDeactivated(address indexed userAddress, uint256 timestamp);
    
    // 修饰符：只有已注册用户可以调用
    modifier onlyRegisteredUser() {
        require(users[msg.sender].isActive, "User not registered or inactive");
        _;
    }
    
    /**
     * @dev 注册新用户
     * @param username 用户名（明文）
     * @param password 密码（明文）
     */
    function register(string memory username, string memory password) public {
        require(bytes(username).length > 0, "Username cannot be empty");
        require(bytes(password).length > 0, "Password cannot be empty");
        require(!users[msg.sender].isActive, "User already registered");
        
        // 计算用户名和密码的哈希值
        bytes32 usernameHash = keccak256(abi.encodePacked(username));
        bytes32 passwordHash = keccak256(abi.encodePacked(password));
        
        // 检查用户名是否已存在
        require(usernameToAddress[usernameHash] == address(0), "Username already taken");
        
        // 创建用户记录
        users[msg.sender] = User({
            usernameHash: usernameHash,
            passwordHash: passwordHash,
            createdAt: block.timestamp,
            isActive: true
        });
        
        // 建立用户名到地址的映射
        usernameToAddress[usernameHash] = msg.sender;
        
        emit UserRegistered(msg.sender, usernameHash, block.timestamp);
    }
    
    /**
     * @dev 用户登录验证
     * @param username 用户名（明文）
     * @param password 密码（明文）
     * @return success 登录是否成功
     */
    function login(string memory username, string memory password) public view returns (bool success) {
        bytes32 usernameHash = keccak256(abi.encodePacked(username));
        address userAddress = usernameToAddress[usernameHash];
        
        if (userAddress == address(0)) {
            return false; // 用户不存在
        }
        
        User storage user = users[userAddress];
        if (!user.isActive) {
            return false; // 用户未激活
        }
        
        bytes32 inputPasswordHash = keccak256(abi.encodePacked(password));
        return user.passwordHash == inputPasswordHash;
    }
    
    /**
     * @dev 更新密码
     * @param oldPassword 旧密码（明文）
     * @param newPassword 新密码（明文）
     */
    function updatePassword(string memory oldPassword, string memory newPassword) public onlyRegisteredUser {
        require(bytes(newPassword).length > 0, "New password cannot be empty");
        
        bytes32 oldPasswordHash = keccak256(abi.encodePacked(oldPassword));
        require(users[msg.sender].passwordHash == oldPasswordHash, "Old password incorrect");
        
        bytes32 newPasswordHash = keccak256(abi.encodePacked(newPassword));
        users[msg.sender].passwordHash = newPasswordHash;
        
        emit PasswordUpdated(msg.sender, block.timestamp);
    }
    
    /**
     * @dev 获取用户信息（不包含敏感数据）
     * @return usernameHash 用户名哈希
     * @return createdAt 创建时间
     * @return isActive 是否激活
     */
    function getUserInfo() public view onlyRegisteredUser returns (bytes32 usernameHash, uint256 createdAt, bool isActive) {
        User storage user = users[msg.sender];
        return (user.usernameHash, user.createdAt, user.isActive);
    }
    
    /**
     * @dev 停用用户账户
     */
    function deactivateAccount() public onlyRegisteredUser {
        users[msg.sender].isActive = false;
        emit UserDeactivated(msg.sender, block.timestamp);
    }
    
    /**
     * @dev 检查用户名是否可用
     * @param username 用户名（明文）
     * @return available 是否可用
     */
    function isUsernameAvailable(string memory username) public view returns (bool available) {
        bytes32 usernameHash = keccak256(abi.encodePacked(username));
        return usernameToAddress[usernameHash] == address(0);
    }
    
    /**
     * @dev 获取注册用户总数
     * @return count 用户总数
     */
    function getTotalUsers() public view returns (uint256 count) {
        // 注意：这个函数在实际生产环境中可能很昂贵
        // 这里仅作为演示
        return 0; // 简化实现，实际需要维护一个计数器
    }
}
