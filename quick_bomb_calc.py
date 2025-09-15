#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速投弹计算脚本
直接输入参数进行投弹时刻计算
"""

import sys
import os
from typing import Dict, Any

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bomb_release_calculator import BombReleaseCalculator, Position, SpeedData

def quick_bomb_calculation(
    aircraft_lat: float, aircraft_lon: float, aircraft_alt: float,
    target_lat: float, target_lon: float, target_alt: float,
    airspeed: float, groundspeed: float
) -> Dict[str, Any]:
    """
    快速投弹计算
    
    Args:
        aircraft_lat: 飞机纬度 (度)
        aircraft_lon: 飞机经度 (度)
        aircraft_alt: 飞机高度 (米)
        target_lat: 目标纬度 (度)
        target_lon: 目标经度 (度)
        target_alt: 目标高度 (米)
        airspeed: 空速 (m/s)
        groundspeed: 地速 (m/s)
        
    Returns:
        计算结果字典
    """
    try:
        # 创建计算器
        calculator = BombReleaseCalculator()
        
        # 创建位置对象
        aircraft_pos = Position(aircraft_lat, aircraft_lon, aircraft_alt)
        target_pos = Position(target_lat, target_lon, target_alt)
        
        # 创建速度对象
        speed_data = SpeedData(airspeed, groundspeed)
        
        # 执行计算
        result = calculator.calculate_release_point(aircraft_pos, target_pos, speed_data)
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error_code': 'EXCEPTION',
            'message': f'计算过程出现异常: {str(e)}'
        }


def print_result(result: Dict[str, Any]):
    """打印格式化的结果"""
    print("\n" + "="*50)
    print("🎯 投弹计算结果")
    print("="*50)
    
    if result['success']:
        print("✅ 计算成功!")
        print(f"📍 投弹倒计时: {result['release_time']:.2f} 秒")
        print(f"📏 提前距离: {result['release_distance']:.0f} 米")
        print(f"⏱️ 飞行时间: {result['flight_time']:.2f} 秒")
        print(f"💨 风速影响: {result['wind_speed']:.1f} m/s")
        
        if 'calculations' in result:
            calc = result['calculations']
            print(f"\n📊 详细信息:")
            print(f"   目标距离: {calc.get('target_distance', 0):.0f} 米")
            print(f"   目标方位: {calc.get('target_bearing', 0):.1f}°")
            print(f"   高度差: {calc.get('altitude_difference', 0):.0f} 米")
        
        print(f"\n🎯 操作建议:")
        print(f"   在 {result['release_time']:.1f} 秒后投弹")
        print(f"   或在距离目标 {result['release_distance']:.0f} 米时投弹")
        
    else:
        print("❌ 计算失败!")
        print(f"错误信息: {result['message']}")


def interactive_mode():
    """交互式输入模式"""
    print("🎯 固定翼飞机投弹计算器 - 交互模式")
    print("="*50)
    
    try:
        print("\n📍 请输入飞机当前位置:")
        aircraft_lat = float(input("飞机纬度 (度): "))
        aircraft_lon = float(input("飞机经度 (度): "))
        aircraft_alt = float(input("飞机高度 (米): "))
        
        print("\n🎯 请输入目标位置:")
        target_lat = float(input("目标纬度 (度): "))
        target_lon = float(input("目标经度 (度): "))
        target_alt = float(input("目标高度 (米): "))
        
        print("\n🛩️ 请输入飞行速度:")
        airspeed = float(input("空速 (m/s): "))
        groundspeed = float(input("地速 (m/s): "))
        
        print("\n🧮 正在计算...")
        result = quick_bomb_calculation(
            aircraft_lat, aircraft_lon, aircraft_alt,
            target_lat, target_lon, target_alt,
            airspeed, groundspeed
        )
        
        print_result(result)
        
    except ValueError as e:
        print(f"❌ 输入错误: {e}")
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"❌ 程序错误: {e}")


def demo_mode():
    """演示模式（使用预设数据）"""
    print("🎯 固定翼飞机投弹计算器 - 演示模式")
    print("="*50)
    
    # 演示数据
    demo_data = {
        'aircraft_lat': 22.3193,   # 深圳
        'aircraft_lon': 114.1694,
        'aircraft_alt': 500.0,     # 500米高度
        'target_lat': 22.3293,     # 目标位置
        'target_lon': 114.1794,
        'target_alt': 0.0,         # 地面目标
        'airspeed': 50.0,          # 50 m/s 空速
        'groundspeed': 45.0        # 45 m/s 地速
    }
    
    print("\n📊 使用演示数据:")
    print(f"   飞机位置: {demo_data['aircraft_lat']:.4f}, {demo_data['aircraft_lon']:.4f}, {demo_data['aircraft_alt']:.0f}m")
    print(f"   目标位置: {demo_data['target_lat']:.4f}, {demo_data['target_lon']:.4f}, {demo_data['target_alt']:.0f}m")
    print(f"   空速: {demo_data['airspeed']:.0f} m/s, 地速: {demo_data['groundspeed']:.0f} m/s")
    
    print("\n🧮 正在计算...")
    result = quick_bomb_calculation(**demo_data)
    
    print_result(result)


def command_line_mode():
    """命令行参数模式"""
    if len(sys.argv) != 9:
        print("使用方法:")
        print("python quick_bomb_calc.py <飞机纬度> <飞机经度> <飞机高度> <目标纬度> <目标经度> <目标高度> <空速> <地速>")
        print("\n示例:")
        print("python quick_bomb_calc.py 22.3193 114.1694 500 22.3293 114.1794 0 50 45")
        return
    
    try:
        args = [float(arg) for arg in sys.argv[1:]]
        
        result = quick_bomb_calculation(*args)
        print_result(result)
        
    except ValueError:
        print("❌ 参数格式错误，请输入数字")
    except Exception as e:
        print(f"❌ 计算错误: {e}")


def main():
    """主函数"""
    print("🎯 固定翼飞机投弹时刻计算器")
    print("="*50)
    
    if len(sys.argv) > 1:
        # 命令行模式
        command_line_mode()
    else:
        # 交互模式选择
        print("请选择运行模式:")
        print("1. 交互式输入")
        print("2. 演示模式")
        print("3. 退出")
        
        try:
            choice = input("\n请输入选择 (1-3): ").strip()
            
            if choice == '1':
                interactive_mode()
            elif choice == '2':
                demo_mode()
            elif choice == '3':
                print("👋 再见!")
            else:
                print("❌ 无效选择")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户取消操作")


if __name__ == "__main__":
    main()
