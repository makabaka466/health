// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SimpleUserFlow
 * @dev 最小化用户注册流程示例（学习版）
 * 目的：帮助你快速理解“注册 -> 更新资料 -> 查询”的完整链上调用流程
 */
contract SimpleUserFlow {
    // 用户信息（为了教学简单，直接存字符串）
    struct UserProfile {
        string nickname;      // 昵称
        uint256 createdAt;    // 注册时间
        bool exists;          // 是否已注册
    }

    // 地址 => 用户资料
    mapping(address => UserProfile) private users;

    // 事件：前端可监听
    event UserRegistered(address indexed user, string nickname, uint256 timestamp);
    event NicknameUpdated(address indexed user, string oldNickname, string newNickname, uint256 timestamp);

    /**
     * @dev 注册
     * 要求：当前地址未注册，昵称非空
     */
    function register(string memory nickname) external {
        require(!users[msg.sender].exists, "Already registered");
        require(bytes(nickname).length > 0, "Nickname cannot be empty");

        users[msg.sender] = UserProfile({
            nickname: nickname,
            createdAt: block.timestamp,
            exists: true
        });

        emit UserRegistered(msg.sender, nickname, block.timestamp);
    }

    /**
     * @dev 更新昵称
     */
    function updateNickname(string memory newNickname) external {
        require(users[msg.sender].exists, "Not registered");
        require(bytes(newNickname).length > 0, "Nickname cannot be empty");

        string memory oldNickname = users[msg.sender].nickname;
        users[msg.sender].nickname = newNickname;

        emit NicknameUpdated(msg.sender, oldNickname, newNickname, block.timestamp);
    }

    /**
     * @dev 查询自己的资料
     */
    function getMyProfile()
        external
        view
        returns (
            string memory nickname,
            uint256 createdAt,
            bool exists
        )
    {
        UserProfile storage user = users[msg.sender];
        return (user.nickname, user.createdAt, user.exists);
    }

    /**
     * @dev 查询任意地址是否已注册（用于演示）
     */
    function isRegistered(address userAddress) external view returns (bool) {
        return users[userAddress].exists;
    }
}
