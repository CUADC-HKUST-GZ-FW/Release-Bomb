#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投弹计算程序测试脚本
快速验证程序功能的简化测试
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """测试基础功能"""
    print("🧪 测试基础计算功能...")
    
    try:
        from bomb_release_calculator import BombReleaseCalculator, Position, SpeedData
        
        # 创建计算器
        calculator = BombReleaseCalculator()
        
        # 设置测试数据
        aircraft = Position(22.3193, 114.1694, 500.0)
        target = Position(22.3293, 114.1794, 0.0)
        speed = SpeedData(50.0, 45.0)
        
        # 执行计算
        result = calculator.calculate_release_point(aircraft, target, speed)
        
        if result['success']:
            print("✅ 基础功能测试通过")
            print(f"   投弹时间: {result['release_time']:.2f}秒")
            print(f"   投弹距离: {result['release_distance']:.0f}米")
            return True
        else:
            print(f"❌ 计算失败: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ 基础功能测试失败: {e}")
        return False


def test_input_validation():
    """测试输入验证"""
    print("\n🧪 测试输入验证...")
    
    try:
        from bomb_release_calculator import Position, SpeedData
        
        # 测试无效坐标
        try:
            Position(200.0, 114.1694, 500.0)  # 无效纬度
            print("❌ 坐标验证失败 - 应该抛出异常")
            return False
        except ValueError:
            print("✅ 坐标验证通过")
        
        # 测试无效速度
        try:
            SpeedData(-10.0, 45.0)  # 无效空速
            print("❌ 速度验证失败 - 应该抛出异常")
            return False
        except ValueError:
            print("✅ 速度验证通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 输入验证测试失败: {e}")
        return False


def test_error_handling():
    """测试错误处理"""
    print("\n🧪 测试错误处理...")
    
    try:
        from bomb_release_calculator import BombReleaseCalculator, Position, SpeedData
        
        calculator = BombReleaseCalculator()
        
        # 测试高度过低的情况
        aircraft = Position(22.3193, 114.1694, 10.0)  # 高度过低
        target = Position(22.3293, 114.1794, 0.0)
        speed = SpeedData(50.0, 45.0)
        
        result = calculator.calculate_release_point(aircraft, target, speed)
        
        if not result['success']:
            print("✅ 错误处理测试通过")
            print(f"   正确捕获错误: {result['message']}")
            return True
        else:
            print("❌ 错误处理失败 - 应该返回失败结果")
            return False
            
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")
        return False


def test_mavlink_availability():
    """测试MAVLink模块可用性"""
    print("\n🧪 测试MAVLink模块...")
    
    try:
        import pymavlink
        print("✅ pymavlink库可用")
        
        try:
            from mavlink_integration import BombReleaseController
            print("✅ MAVLink集成模块可用")
            return True
        except ImportError as e:
            print(f"⚠️ MAVLink集成模块导入失败: {e}")
            return False
            
    except ImportError:
        print("⚠️ pymavlink库未安装")
        print("   安装命令: pip install pymavlink")
        return False


def run_all_tests():
    """运行所有测试"""
    print("🎯 固定翼飞机投弹计算程序 - 功能测试")
    print("=" * 50)
    
    tests = [
        ("基础功能", test_basic_functionality),
        ("输入验证", test_input_validation),
        ("错误处理", test_error_handling),
        ("MAVLink可用性", test_mavlink_availability)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}测试:")
        try:
            if test_func():
                passed += 1
            else:
                print(f"   测试未通过")
        except Exception as e:
            print(f"   测试出现异常: {e}")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！程序运行正常")
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
