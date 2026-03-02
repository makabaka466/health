// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/*
 * 新手阅读指南：
 * 1) mapping 可以理解为“链上的哈希表/字典”。
 *    - users[address] => 某个地址对应的用户信息
 *    - usernameToAddress[usernameHash] => 用户名哈希反查地址
 * 2) keccak256(...) 是 Solidity 常用哈希函数，用于把明文变成定长摘要。
 * 3) require(条件, "错误信息")：条件不满足就回滚交易并抛错。
 * 4) onlyRegisteredUser 是“修饰符 modifier”，相当于函数执行前先做权限检查。
 * 5) 这个合约用于教学演示：链上哈希并不等于完整生产级认证方案。
 */

/**
 * @title UserAuth
 * @dev 智能合约用于安全存储用户认证信息
 * 注意：在实际生产环境中，不应该在区块链上存储明文密码
 * 这里仅作为演示，实际应用应该使用密码哈希值
 */
contract UserAuth {

    // 用户资料状态：私密或公开
    enum ProfileStatus {
        Private,
        Public
    }

    // 用户结构体：只保存哈希，不保存明文
    struct User {
        bytes32 usernameHash;     // 用户名的哈希值
        bytes32 passwordHash;     // 密码的哈希值（不是明文）
        uint256 createdAt;        // 创建时间
        bool isActive;           // 账户是否激活
        bytes32 profileDataHash;  // 用户资料哈希（可对应链下加密资料）
        bytes32 publicKeyHash;    // 用户加密公钥的哈希（用于密钥轮换校验）
        ProfileStatus profileStatus; // 资料公开/私密状态
    }
    
    // 用户地址 => 用户信息
    mapping(address => User) public users;
    
    // 用户名哈希 => 地址（用于检查用户名是否冲突）
    mapping(bytes32 => address) public usernameToAddress;

    // 统计计数器
    uint256 private totalUsers;
    uint256 private activeUsers;
    
    // 事件
    event UserRegistered(address indexed userAddress, bytes32 indexed usernameHash, uint256 timestamp);
    event UserLoggedIn(address indexed userAddress, uint256 timestamp);
    event PasswordUpdated(address indexed userAddress, uint256 timestamp);
    event UserDeactivated(address indexed userAddress, uint256 timestamp);
    event UserProfileUpdated(address indexed userAddress, bytes32 profileDataHash, bytes32 publicKeyHash, uint256 timestamp);
    event UserProfileStatusChanged(address indexed userAddress, ProfileStatus oldStatus, ProfileStatus newStatus, uint256 timestamp);
    
    // 修饰符：仅激活状态的已注册用户可调用
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
        
        // 计算用户名和密码哈希（上链前做摘要）
        bytes32 usernameHash = keccak256(abi.encodePacked(username));
        bytes32 passwordHash = keccak256(abi.encodePacked(password));
        
        // 检查用户名是否已存在
        require(usernameToAddress[usernameHash] == address(0), "Username already taken");
        
        // 创建用户记录
        users[msg.sender] = User({
            usernameHash: usernameHash,
            passwordHash: passwordHash,
            createdAt: block.timestamp,
            isActive: true,
            profileDataHash: bytes32(0),
            publicKeyHash: bytes32(0),
            profileStatus: ProfileStatus.Private
        });
        
        // 建立用户名哈希到地址的映射，便于登录时按用户名查用户
        usernameToAddress[usernameHash] = msg.sender;

        totalUsers += 1;
        activeUsers += 1;
        
        emit UserRegistered(msg.sender, usernameHash, block.timestamp);
    }

    /**
     * @dev 注册用户并附带资料哈希与公钥哈希
     * @param username 用户名（明文）
     * @param password 密码（明文）
     * @param profileDataHash 用户资料哈希
     * @param publicKeyHash 用户公钥哈希
     */
    function registerWithProfile(
        string memory username,
        string memory password,
        bytes32 profileDataHash,
        bytes32 publicKeyHash
    ) public {
        register(username, password);
        users[msg.sender].profileDataHash = profileDataHash;
        users[msg.sender].publicKeyHash = publicKeyHash;

        emit UserProfileUpdated(msg.sender, profileDataHash, publicKeyHash, block.timestamp);
    }
    
    /**
     * @dev 用户登录验证
     * @param username 用户名（明文）
     * @param password 密码（明文）
     * @return success 登录是否成功
     */
    function login(string memory username, string memory password) public view returns (bool success) {
        // 登录流程：用户名 -> 地址 -> 比较密码哈希
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
     * @dev 更新用户资料哈希和公钥哈希
     * @param profileDataHash 用户资料哈希
     * @param publicKeyHash 用户公钥哈希
     */
    function updateUserProfile(bytes32 profileDataHash, bytes32 publicKeyHash) public onlyRegisteredUser {
        users[msg.sender].profileDataHash = profileDataHash;
        users[msg.sender].publicKeyHash = publicKeyHash;

        emit UserProfileUpdated(msg.sender, profileDataHash, publicKeyHash, block.timestamp);
    }

    /**
     * @dev 将用户资料设为公开
     */
    function makeProfilePublic() public onlyRegisteredUser {
        User storage user = users[msg.sender];
        require(user.profileStatus == ProfileStatus.Private, "Profile already public");

        ProfileStatus oldStatus = user.profileStatus;
        user.profileStatus = ProfileStatus.Public;

        emit UserProfileStatusChanged(msg.sender, oldStatus, ProfileStatus.Public, block.timestamp);
    }

    /**
     * @dev 将用户资料设为私密
     */
    function makeProfilePrivate() public onlyRegisteredUser {
        User storage user = users[msg.sender];
        require(user.profileStatus == ProfileStatus.Public, "Profile already private");

        ProfileStatus oldStatus = user.profileStatus;
        user.profileStatus = ProfileStatus.Private;

        emit UserProfileStatusChanged(msg.sender, oldStatus, ProfileStatus.Private, block.timestamp);
    }
    
    /**
     * @dev 更新密码
     * @param oldPassword 旧密码（明文）
     * @param newPassword 新密码（明文）
     */
    function updatePassword(string memory oldPassword, string memory newPassword) public onlyRegisteredUser {
        require(bytes(newPassword).length > 0, "New password cannot be empty");
        
        // 先校验旧密码哈希，再更新新密码哈希
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
     * @dev 获取当前用户完整资料信息
     */
    function getMyProfileInfo()
        public
        view
        onlyRegisteredUser
        returns (
            bytes32 usernameHash,
            uint256 createdAt,
            bool isActive,
            bytes32 profileDataHash,
            bytes32 publicKeyHash,
            ProfileStatus profileStatus
        )
    {
        User storage user = users[msg.sender];
        return (
            user.usernameHash,
            user.createdAt,
            user.isActive,
            user.profileDataHash,
            user.publicKeyHash,
            user.profileStatus
        );
    }

    /**
     * @dev 读取公开用户资料（仅在用户激活且资料为公开时可读）
     * @param userAddress 目标用户地址
     */
    function getPublicUserProfile(address userAddress)
        public
        view
        returns (
            bytes32 usernameHash,
            bytes32 profileDataHash,
            bytes32 publicKeyHash,
            uint256 createdAt
        )
    {
        User storage user = users[userAddress];
        require(user.isActive, "User inactive or not found");
        require(user.profileStatus == ProfileStatus.Public, "Profile is private");

        return (user.usernameHash, user.profileDataHash, user.publicKeyHash, user.createdAt);
    }

    /**
     * @dev 检查 requester 是否可访问 userAddress 的资料
     */
    function checkUserDataAccess(address requester, address userAddress) public view returns (bool) {
        User storage user = users[userAddress];
        if (!user.isActive) {
            return false;
        }

        if (requester == userAddress) {
            return true;
        }

        return user.profileStatus == ProfileStatus.Public;
    }
    
    /**
     * @dev 停用用户账户
     */
    function deactivateAccount() public onlyRegisteredUser {
        // 停用后仍保留历史数据，只是 isActive=false
        users[msg.sender].isActive = false;
        if (activeUsers > 0) {
            activeUsers -= 1;
        }
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
        return totalUsers;
    }

    /**
     * @dev 获取激活状态用户数量
     */
    function getActiveUsers() public view returns (uint256 count) {
        return activeUsers;
    }

    /**
     * @dev 检查地址是否注册且激活
     */
    function isUserActive(address userAddress) public view returns (bool) {
        return users[userAddress].isActive;
    }
}
