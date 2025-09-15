#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台兼容性工具
处理Windows和Linux系统之间的差异
"""

import os
import sys
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional

class PlatformCompat:
    """平台兼容性处理类"""
    
    @staticmethod
    def is_windows() -> bool:
        """是否为Windows系统"""
        return platform.system().lower() == 'windows'
    
    @staticmethod
    def is_linux() -> bool:
        """是否为Linux系统"""
        return platform.system().lower() == 'linux'
    
    @staticmethod
    def get_serial_ports() -> List[str]:
        """获取可用的串口设备"""
        ports = []
        
        if PlatformCompat.is_windows():
            # Windows串口
            for i in range(1, 21):  # COM1 到 COM20
                ports.append(f"COM{i}")
        
        elif PlatformCompat.is_linux():
            # Linux串口设备
            common_ports = [
                "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyUSB2",
                "/dev/ttyAMA0", "/dev/ttyAMA1",
                "/dev/ttyS0", "/dev/ttyS1", "/dev/ttyS2",
                "/dev/ttyACM0", "/dev/ttyACM1"
            ]
            
            # 只返回存在的设备
            for port in common_ports:
                if os.path.exists(port):
                    ports.append(port)
        
        return ports
    
    @staticmethod
    def get_log_path() -> str:
        """获取日志文件路径"""
        if PlatformCompat.is_windows():
            # Windows: 使用当前目录或临时目录
            return os.path.join(os.getcwd(), "bomb_release.log")
        else:
            # Linux: 使用/tmp或/var/log
            if os.access("/var/log", os.W_OK):
                return "/var/log/bomb_release.log"
            else:
                return "/tmp/bomb_release.log"
    
    @staticmethod
    def get_config_path() -> str:
        """获取配置文件路径"""
        current_dir = Path(__file__).parent
        
        if PlatformCompat.is_linux():
            return str(current_dir / "config_linux.json")
        else:
            return str(current_dir / "config.json")
    
    @staticmethod
    def get_pid_path() -> str:
        """获取PID文件路径"""
        if PlatformCompat.is_windows():
            return os.path.join(os.getcwd(), "bomb_release.pid")
        else:
            return "/tmp/bomb_release.pid"
    
    @staticmethod
    def get_mavlink_connections() -> List[str]:
        """获取MAVLink连接字符串"""
        connections = ["udp:127.0.0.1:14550"]  # 通用UDP连接
        
        # 添加串口连接
        serial_ports = PlatformCompat.get_serial_ports()
        connections.extend(serial_ports)
        
        if PlatformCompat.is_linux():
            # Linux特定连接
            connections.extend([
                "udp:0.0.0.0:14550",
                "tcp:127.0.0.1:5760"
            ])
        
        return connections
    
    @staticmethod
    def setup_permissions():
        """设置文件权限（Linux）"""
        if not PlatformCompat.is_linux():
            return True
        
        try:
            current_dir = Path(__file__).parent
            
            # 设置脚本可执行权限
            scripts = [
                "start_bomb_release.sh",
                "install_service.sh"
            ]
            
            for script in scripts:
                script_path = current_dir / script
                if script_path.exists():
                    os.chmod(script_path, 0o755)
            
            return True
            
        except Exception as e:
            print(f"设置权限失败: {e}")
            return False
    
    @staticmethod
    def check_dependencies() -> Dict[str, bool]:
        """检查依赖包"""
        dependencies = {
            'pymavlink': False,
            'numpy': False
        }
        
        try:
            import pymavlink
            dependencies['pymavlink'] = True
        except ImportError:
            pass
        
        try:
            import numpy
            dependencies['numpy'] = True
        except ImportError:
            pass
        
        return dependencies


def create_platform_config():
    """创建平台特定配置"""
    config = {
        "system": {
            "platform": platform.system().lower(),
            "architecture": platform.machine(),
            "python_version": sys.version,
            "log_path": PlatformCompat.get_log_path(),
            "pid_file": PlatformCompat.get_pid_path()
        },
        "mavlink_settings": {
            "available_connections": PlatformCompat.get_mavlink_connections(),
            "default_connection": PlatformCompat.get_mavlink_connections()[0],
            "connection_timeout": 10,
            "message_timeout": 5,
            "auto_reconnect": True,
            "reconnect_interval": 5
        },
        "calculation_settings": {
            "max_target_distance": 50000,
            "min_release_height": 50,
            "max_flight_time": 60,
            "convergence_tolerance": 1e-6,
            "max_iterations": 1000
        },
        "performance": {
            "enable_optimization": True,
            "use_fast_math": True,
            "low_memory_mode": PlatformCompat.is_linux()
        }
    }
    
    # 保存配置
    config_path = PlatformCompat.get_config_path()
    
    import json
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 平台配置已创建: {config_path}")
    return config


def check_system_readiness():
    """检查系统准备状态"""
    print("🔍 系统准备状态检查")
    print("=" * 40)
    
    # 基本系统信息
    print(f"操作系统: {platform.system()}")
    print(f"平台: {platform.platform()}")
    print(f"架构: {platform.machine()}")
    print(f"Python版本: {sys.version}")
    
    # 检查依赖
    print(f"\n📦 依赖检查:")
    deps = PlatformCompat.check_dependencies()
    for dep, available in deps.items():
        status = "✅" if available else "❌"
        print(f"   {dep}: {status}")
    
    # 检查串口
    print(f"\n📡 可用串口:")
    ports = PlatformCompat.get_serial_ports()
    if ports:
        for port in ports[:5]:  # 只显示前5个
            exists = "✅" if (PlatformCompat.is_linux() and os.path.exists(port)) else "❓"
            print(f"   {port}: {exists}")
    else:
        print("   未找到串口设备")
    
    # 检查路径
    print(f"\n📁 路径配置:")
    print(f"   日志路径: {PlatformCompat.get_log_path()}")
    print(f"   配置路径: {PlatformCompat.get_config_path()}")
    print(f"   PID路径: {PlatformCompat.get_pid_path()}")
    
    # 权限检查（Linux）
    if PlatformCompat.is_linux():
        print(f"\n🔐 权限设置:")
        if PlatformCompat.setup_permissions():
            print("   ✅ 权限设置成功")
        else:
            print("   ❌ 权限设置失败")
    
    return all(deps.values())


def main():
    """主函数"""
    print("🔧 跨平台兼容性工具")
    print("=" * 40)
    
    # 检查系统状态
    ready = check_system_readiness()
    
    # 创建平台配置
    config = create_platform_config()
    
    if ready:
        print("\n🎉 系统检查完成，所有依赖可用！")
    else:
        print("\n⚠️ 系统检查完成，部分依赖缺失")
        print("请运行: pip install -r requirements.txt")
    
    return ready


if __name__ == "__main__":
    main()
