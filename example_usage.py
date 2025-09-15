#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投弹计算程序使用示例
演示如何安全可靠地使用投弹计算系统
"""

import time
import json
from typing import Dict, Any

# 导入核心模块
from bomb_release_calculator import (
    BombReleaseCalculator, Position, SpeedData, ErrorCode
)

# 尝试导入MAVLink集成模块
try:
    from mavlink_integration import BombReleaseController
    MAVLINK_AVAILABLE = True
except ImportError:
    MAVLINK_AVAILABLE = False
    print("警告: MAVLink模块不可用，将使用模拟数据模式")


def simulate_mavlink_data() -> Dict[str, float]:
    """
    模拟MAVLink数据（用于测试）
    实际使用时，这些数据来自pymavlink
    """
    # 模拟VFR_HUD消息数据
    return {
        'airspeed': 50.0,      # 空速 m/s
        'groundspeed': 45.0,   # 地速 m/s
        'latitude': 22.3193,   # 纬度（深圳）
        'longitude': 114.1694, # 经度（深圳）
        'altitude': 500.0      # 高度 m
    }


def example_basic_calculation():
    """基础计算示例（不需要MAVLink）"""
    print("\n🧮 基础投弹计算示例")
    print("-" * 30)
    
    try:
        # 创建计算器
        calculator = BombReleaseCalculator()
        
        # 设置飞机位置（当前位置）
        aircraft_pos = Position(
            latitude=22.3193,    # 深圳纬度
            longitude=114.1694,  # 深圳经度
            altitude=500.0       # 飞行高度500米
        )
        
        # 设置目标位置
        target_pos = Position(
            latitude=22.3293,    # 目标纬度（向北1公里）
            longitude=114.1794,  # 目标经度（向东1公里）
            altitude=0.0         # 目标在地面
        )
        
        # 设置速度数据
        speed_data = SpeedData(
            airspeed=50.0,      # 空速50 m/s
            groundspeed=45.0    # 地速45 m/s（有5 m/s逆风）
        )
        
        # 执行计算
        result = calculator.calculate_release_point(
            aircraft_pos, target_pos, speed_data
        )
        
        # 显示结果
        print_calculation_result(result)
        
    except Exception as e:
        print(f"❌ 基础计算示例失败: {e}")


def example_with_mavlink_simulation():
    """使用模拟MAVLink数据的示例"""
    print("\n📡 MAVLink模拟数据示例")
    print("-" * 30)
    
    try:
        # 获取模拟的MAVLink数据
        mavlink_data = simulate_mavlink_data()
        
        # 创建计算器
        calculator = BombReleaseCalculator()
        
        # 验证速度数据
        is_valid, error_msg = calculator.validate_mavlink_data(
            mavlink_data['airspeed'], 
            mavlink_data['groundspeed']
        )
        
        if not is_valid:
            print(f"❌ 速度数据验证失败: {error_msg}")
            return
        
        # 创建位置和速度对象
        aircraft_pos = Position(
            latitude=mavlink_data['latitude'],
            longitude=mavlink_data['longitude'],
            altitude=mavlink_data['altitude']
        )
        
        speed_data = SpeedData(
            airspeed=mavlink_data['airspeed'],
            groundspeed=mavlink_data['groundspeed']
        )
        
        # 设置目标位置（距离飞机约1.5公里）
        target_pos = Position(
            latitude=22.3350,    # 向北约1.7公里
            longitude=114.1850,  # 向东约1.7公里
            altitude=50.0        # 目标高度50米
        )
        
        print(f"飞机位置: {aircraft_pos.latitude:.4f}, {aircraft_pos.longitude:.4f}, {aircraft_pos.altitude}m")
        print(f"目标位置: {target_pos.latitude:.4f}, {target_pos.longitude:.4f}, {target_pos.altitude}m")
        print(f"空速: {speed_data.airspeed} m/s, 地速: {speed_data.groundspeed} m/s")
        
        # 执行计算
        result = calculator.calculate_release_point(
            aircraft_pos, target_pos, speed_data
        )
        
        # 显示结果
        print_calculation_result(result)
        
    except Exception as e:
        print(f"❌ MAVLink模拟示例失败: {e}")


def example_real_mavlink():
    """真实MAVLink连接示例"""
    print("\n🔗 真实MAVLink连接示例")
    print("-" * 30)
    
    if not MAVLINK_AVAILABLE:
        print("❌ MAVLink模块不可用，请安装pymavlink: pip install pymavlink")
        return
    
    try:
        # 创建投弹控制器
        controller = BombReleaseController("udp:127.0.0.1:14550")
        
        print("正在尝试连接到飞机...")
        
        # 尝试连接（较短超时，因为这可能是演示环境）
        if controller.connect_to_aircraft(timeout=3.0):
            print("✅ 成功连接到飞机")
            
            # 设置目标位置
            target_pos = Position(
                latitude=22.3350,
                longitude=114.1850,
                altitude=0.0
            )
            
            # 计算投弹参数
            print("正在获取飞行数据并计算投弹参数...")
            result = controller.calculate_bomb_release(target_pos)
            
            # 显示结果
            print_calculation_result(result)
            
            # 显示系统状态
            status = controller.get_status()
            print(f"\n📊 系统状态:")
            print(f"   连接状态: {'已连接' if status['mavlink_connected'] else '未连接'}")
            print(f"   计算次数: {status['calculation_count']}")
            
        else:
            print("❌ 无法连接到飞机（这在演示环境中是正常的）")
            print("💡 提示: 确保有飞行模拟器或真实飞机在指定端口提供MAVLink数据")
            
    except Exception as e:
        print(f"❌ 真实MAVLink示例失败: {e}")
    finally:
        try:
            controller.cleanup()
        except:
            pass


def example_error_handling():
    """错误处理示例"""
    print("\n⚠️ 错误处理示例")
    print("-" * 30)
    
    calculator = BombReleaseCalculator()
    
    # 测试无效输入
    test_cases = [
        {
            'name': '飞行高度过低',
            'aircraft': Position(latitude=22.3193, longitude=114.1694, altitude=10.0),
            'target': Position(latitude=22.3293, longitude=114.1794, altitude=0.0),
            'speed': SpeedData(airspeed=50.0, groundspeed=45.0)
        },
        {
            'name': '目标距离过远',
            'aircraft': Position(latitude=22.3193, longitude=114.1694, altitude=500.0),
            'target': Position(latitude=23.0, longitude=115.0, altitude=0.0),  # 很远的目标
            'speed': SpeedData(airspeed=50.0, groundspeed=45.0)
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['name']}")
        try:
            result = calculator.calculate_release_point(
                test_case['aircraft'],
                test_case['target'],
                test_case['speed']
            )
            
            if not result['success']:
                print(f"   ✅ 正确捕获错误: {result['message']}")
                print(f"   错误代码: {result['error_code']}")
            else:
                print(f"   ⚠️ 未预期的成功结果")
                
        except Exception as e:
            print(f"   ✅ 正确抛出异常: {e}")
    
    # 测试无效数据类型创建
    print(f"\n测试 3: 无效坐标创建")
    try:
        Position(latitude=200.0, longitude=114.1694, altitude=500.0)
        print("   ❌ 应该抛出异常")
    except ValueError as e:
        print(f"   ✅ 正确抛出异常: {e}")
    
    print(f"\n测试 4: 无效速度创建")
    try:
        SpeedData(airspeed=-10.0, groundspeed=45.0)
        print("   ❌ 应该抛出异常")
    except ValueError as e:
        print(f"   ✅ 正确抛出异常: {e}")


def print_calculation_result(result: Dict[str, Any]):
    """格式化打印计算结果"""
    print("\n📋 计算结果:")
    print("-" * 20)
    
    if result['success']:
        print("✅ 计算成功!")
        print(f"⏰ 投弹倒计时: {result['release_time']:.2f} 秒")
        print(f"📏 提前投弹距离: {result['release_distance']:.0f} 米")
        print(f"🎯 弹药飞行时间: {result['flight_time']:.2f} 秒")
        print(f"💨 风速影响: {result['wind_speed']:.1f} m/s")
        
        if 'calculations' in result:
            calc = result['calculations']
            print(f"\n📊 详细信息:")
            print(f"   目标距离: {calc.get('target_distance', 0):.0f} 米")
            print(f"   目标方位: {calc.get('target_bearing', 0):.1f}°")
            print(f"   高度差: {calc.get('altitude_difference', 0):.0f} 米")
            
    else:
        print("❌ 计算失败!")
        print(f"错误代码: {result['error_code']}")
        print(f"错误信息: {result['message']}")


def save_calculation_log(result: Dict[str, Any], filename: str = "calculation_log.json"):
    """保存计算日志"""
    try:
        log_entry = {
            'timestamp': time.time(),
            'result': result
        }
        
        # 尝试读取现有日志
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except FileNotFoundError:
            logs = []
        
        # 添加新条目
        logs.append(log_entry)
        
        # 保持最近50条记录
        if len(logs) > 50:
            logs = logs[-50:]
        
        # 保存日志
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
            
        print(f"📝 计算日志已保存到 {filename}")
        
    except Exception as e:
        print(f"⚠️ 保存日志失败: {e}")


def main():
    """主函数 - 运行所有示例"""
    print("🎯 固定翼飞机投弹计算程序 - 完整示例")
    print("=" * 60)
    
    # 运行各种示例
    example_basic_calculation()
    example_with_mavlink_simulation()
    example_error_handling()
    
    # 如果MAVLink可用，运行真实连接示例
    if MAVLINK_AVAILABLE:
        example_real_mavlink()
    else:
        print("\n💡 提示:")
        print("   要使用真实MAVLink功能，请安装依赖:")
        print("   pip install -r requirements.txt")
    
    print("\n✨ 所有示例运行完成!")
    print("\n📖 使用说明:")
    print("   1. 基础使用: 直接调用BombReleaseCalculator")
    print("   2. MAVLink集成: 使用BombReleaseController")
    print("   3. 错误处理: 检查返回结果中的success字段")
    print("   4. 日志记录: 所有操作都会记录到bomb_release.log")


if __name__ == "__main__":
    main()
