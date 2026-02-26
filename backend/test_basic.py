#!/usr/bin/env python3
"""
基本功能测试脚本
测试用户注册、登录、健康数据记录等核心功能
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8000/api"

class HealthSystemTester:
    def __init__(self):
        self.session = None
        self.token = None
        self.user_data = {}
        
    async def setup(self):
        """初始化测试环境"""
        self.session = aiohttp.ClientSession()
        print("🚀 测试环境初始化完成")
        
    async def cleanup(self):
        """清理测试环境"""
        if self.session:
            await self.session.close()
        print("🧹 测试环境清理完成")
        
    async def test_health_check(self):
        """测试健康检查接口"""
        print("\n📋 测试健康检查接口...")
        try:
            async with self.session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 健康检查成功: {data}")
                    return True
                else:
                    print(f"❌ 健康检查失败: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
            
    async def test_user_registration(self):
        """测试用户注册"""
        print("\n👤 测试用户注册...")
        test_user = {
            "username": "testuser123",
            "email": "test123@example.com",
            "password": "test123456"
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/auth/register",
                json=test_user
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 用户注册成功: {data['username']}")
                    self.user_data = test_user
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 用户注册失败: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 用户注册异常: {e}")
            return False
            
    async def test_user_login(self):
        """测试用户登录"""
        print("\n🔐 测试用户登录...")
        if not self.user_data:
            print("❌ 没有用户数据，请先注册")
            return False
            
        login_data = {
            "username": self.user_data["username"],
            "password": self.user_data["password"]
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/auth/login",
                data=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.token = data["access_token"]
                    print(f"✅ 用户登录成功: {data['username']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 用户登录失败: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 用户登录异常: {e}")
            return False
            
    async def test_get_current_user(self):
        """测试获取当前用户信息"""
        print("\n👤 测试获取当前用户信息...")
        if not self.token:
            print("❌ 没有token，请先登录")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            async with self.session.get(
                f"{BASE_URL}/auth/me",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 获取用户信息成功: {data['username']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 获取用户信息失败: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 获取用户信息异常: {e}")
            return False
            
    async def test_health_data_crud(self):
        """测试健康数据CRUD操作"""
        print("\n📊 测试健康数据操作...")
        if not self.token:
            print("❌ 没有token，请先登录")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 1. 创建健康数据
        health_data = {
            "weight": 70.5,
            "height": 175.0,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "heart_rate": 72,
            "blood_sugar": 5.2
        }
        
        try:
            # 创建数据
            async with self.session.post(
                f"{BASE_URL}/health/records",
                json=health_data,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ 创建健康数据失败: {response.status} - {error_text}")
                    return False
                    
                created_data = await response.json()
                record_id = created_data["id"]
                print(f"✅ 创建健康数据成功: ID={record_id}")
                
            # 2. 获取健康数据列表
            async with self.session.get(
                f"{BASE_URL}/health/records",
                headers=headers
            ) as response:
                if response.status == 200:
                    records = await response.json()
                    print(f"✅ 获取健康数据列表成功: 共{len(records)}条记录")
                else:
                    print(f"❌ 获取健康数据列表失败: {response.status}")
                    return False
                    
            # 3. 获取健康数据摘要
            async with self.session.get(
                f"{BASE_URL}/health/summary",
                headers=headers
            ) as response:
                if response.status == 200:
                    summary = await response.json()
                    print(f"✅ 获取健康数据摘要成功: {summary}")
                else:
                    print(f"❌ 获取健康数据摘要失败: {response.status}")
                    return False
                    
            # 4. 更新健康数据
            update_data = {"weight": 71.0}
            async with self.session.put(
                f"{BASE_URL}/health/records/{record_id}",
                json=update_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    updated_data = await response.json()
                    print(f"✅ 更新健康数据成功: 体重更新为{updated_data['weight']}")
                else:
                    print(f"❌ 更新健康数据失败: {response.status}")
                    return False
                    
            # 5. 删除健康数据
            async with self.session.delete(
                f"{BASE_URL}/health/records/{record_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    print(f"✅ 删除健康数据成功")
                else:
                    print(f"❌ 删除健康数据失败: {response.status}")
                    return False
                    
            return True
            
        except Exception as e:
            print(f"❌ 健康数据操作异常: {e}")
            return False
            
    async def test_ai_chat(self):
        """测试AI聊天功能"""
        print("\n🤖 测试AI聊天功能...")
        if not self.token:
            print("❌ 没有token，请先登录")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # 发送消息给AI
            chat_data = {"message": "什么是正常的血压范围？"}
            async with self.session.post(
                f"{BASE_URL}/ai/chat",
                json=chat_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    ai_response = await response.json()
                    print(f"✅ AI聊天成功: {ai_response['reply'][:50]}...")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ AI聊天失败: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ AI聊天异常: {e}")
            return False
            
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始运行健康管理系统基本功能测试")
        print("=" * 50)
        
        await self.setup()
        
        tests = [
            ("健康检查", self.test_health_check),
            ("用户注册", self.test_user_registration),
            ("用户登录", self.test_user_login),
            ("获取用户信息", self.test_get_current_user),
            ("健康数据操作", self.test_health_data_crud),
            ("AI聊天", self.test_ai_chat),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if await test_func():
                    passed += 1
            except Exception as e:
                print(f"❌ {test_name}测试异常: {e}")
                
        await self.cleanup()
        
        print("\n" + "=" * 50)
        print(f"📊 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有测试通过！系统基本功能正常")
        else:
            print("⚠️  部分测试失败，请检查相关功能")
            
        return passed == total

async def main():
    """主函数"""
    tester = HealthSystemTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✨ 系统已准备就绪，可以开始使用！")
    else:
        print("\n🔧 请检查系统配置和依赖安装")

if __name__ == "__main__":
    asyncio.run(main())
