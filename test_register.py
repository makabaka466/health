#!/usr/bin/env python3
"""
注册功能测试脚本
测试用户注册和登录流程
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://127.0.0.1:8000/api"

async def test_register():
    """测试用户注册"""
    print("🧪 测试用户注册功能...")
    
    test_user = {
        "username": "testuser2024",
        "email": "testuser2024@example.com",
        "password": "Test123456!"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 测试注册
            async with session.post(f"{BASE_URL}/auth/register", json=test_user) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 注册成功: {data['username']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 注册失败: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ 注册异常: {e}")
            return False

async def test_login():
    """测试用户登录"""
    print("\n🔐 测试用户登录功能...")
    
    login_data = {
        "username": "testuser2024",
        "password": "Test123456!"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}/auth/login", 
                data=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 登录成功: {data['username']}")
                    print(f"   Token: {data['access_token'][:50]}...")
                    print(f"   Role: {data['role']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 登录失败: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False

async def main():
    """主函数"""
    print("🚀 开始测试注册和登录功能")
    print("=" * 50)
    
    register_success = await test_register()
    
    if register_success:
        login_success = await test_login()
        
        if login_success:
            print("\n🎉 注册和登录功能测试通过！")
            print("\n📱 前端测试步骤:")
            print("1. 访问: http://localhost:3000")
            print("2. 点击 '立即注册'")
            print("3. 填写注册信息:")
            print("   - 用户名: testuser2024")
            print("   - 邮箱: testuser2024@example.com")
            print("   - 密码: Test123456!")
            print("4. 同意服务协议并注册")
            print("5. 注册成功后会自动跳转到登录页面")
            print("6. 使用注册的账号登录")
        else:
            print("\n⚠️  注册成功但登录失败")
    else:
        print("\n❌ 注册功能测试失败")
        print("请检查后端服务是否正常运行")

if __name__ == "__main__":
    asyncio.run(main())
