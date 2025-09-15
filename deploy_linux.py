#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux系统部署脚本
用于在固定翼飞机的Linux小电脑上安装和配置投弹计算程序
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def check_system():
    """检查系统环境"""
    print("🔍 检查系统环境...")
    print(f"操作系统: {platform.system()}")
    print(f"平台: {platform.platform()}")
    print(f"Python版本: {sys.version}")
    print(f"架构: {platform.machine()}")
    
    # 检查是否为Linux系统
    if platform.system() != 'Linux':
        print("⚠️ 警告: 当前不是Linux系统，但程序仍可运行")
    
    return True

def check_python_version():
    """检查Python版本"""
    print("\n🐍 检查Python版本...")
    
    if sys.version_info < (3, 7):
        print("❌ Python版本过低，需要Python 3.7或更高版本")
        return False
    
    print("✅ Python版本满足要求")
    return True

def install_dependencies():
    """安装依赖包"""
    print("\n📦 安装依赖包...")
    
    requirements = [
        "pymavlink>=2.4.0",
        "numpy>=1.21.0"
    ]
    
    for req in requirements:
        try:
            print(f"正在安装 {req}...")
            subprocess.run([sys.executable, "-m", "pip", "install", req], 
                         check=True, capture_output=True, text=True)
            print(f"✅ {req} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ {req} 安装失败: {e}")
            print(f"错误输出: {e.stderr}")
            return False
    
    print("✅ 所有依赖包安装完成")
    return True

def create_service_files():
    """创建Linux服务文件"""
    print("\n🔧 创建Linux系统服务文件...")
    
    # 获取当前脚本目录
    current_dir = Path(__file__).parent.absolute()
    
    # systemd服务文件内容
    service_content = f"""[Unit]
Description=Aircraft Bomb Release Calculator Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory={current_dir}
ExecStart=/usr/bin/python3 {current_dir}/bomb_release_service.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    # 写入服务文件
    service_file = Path("bomb-release.service")
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"✅ 服务文件已创建: {service_file}")
    
    # 创建安装服务的脚本
    install_script = f"""#!/bin/bash
# 安装投弹计算服务

echo "正在安装投弹计算服务..."

# 复制服务文件
sudo cp {service_file} /etc/systemd/system/

# 重新加载systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable bomb-release.service

echo "✅ 服务安装完成"
echo "启动服务: sudo systemctl start bomb-release"
echo "查看状态: sudo systemctl status bomb-release"
echo "查看日志: journalctl -u bomb-release -f"
"""
    
    with open("install_service.sh", 'w') as f:
        f.write(install_script)
    
    # 设置可执行权限
    os.chmod("install_service.sh", 0o755)
    
    print("✅ 服务安装脚本已创建: install_service.sh")
    return True

def create_startup_script():
    """创建启动脚本"""
    print("\n🚀 创建启动脚本...")
    
    startup_script = """#!/bin/bash
# 投弹计算程序启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎯 启动投弹计算程序..."
echo "当前目录: $(pwd)"
echo "时间: $(date)"

# 设置Python路径
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# 检查依赖
echo "检查Python版本..."
python3 --version

echo "检查依赖包..."
python3 -c "import pymavlink; print('pymavlink:', pymavlink.__version__)" 2>/dev/null || echo "⚠️ pymavlink未安装"

# 运行程序
echo "启动投弹计算程序..."
python3 bomb_release_service.py

echo "程序已退出"
"""
    
    with open("start_bomb_release.sh", 'w') as f:
        f.write(startup_script)
    
    os.chmod("start_bomb_release.sh", 0o755)
    
    print("✅ 启动脚本已创建: start_bomb_release.sh")
    return True

def create_config_for_linux():
    """创建Linux特定配置"""
    print("\n⚙️ 创建Linux配置...")
    
    linux_config = {
        "system": {
            "platform": "linux",
            "log_path": "/tmp/bomb_release.log",
            "pid_file": "/tmp/bomb_release.pid"
        },
        "mavlink_settings": {
            "default_connection": "/dev/ttyUSB0",  # Linux串口
            "alternative_connections": [
                "/dev/ttyAMA0",  # 树莓派串口
                "/dev/ttyS0",    # 标准串口
                "udp:127.0.0.1:14550"  # UDP备用
            ],
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
            "low_memory_mode": True
        }
    }
    
    import json
    with open("config_linux.json", 'w') as f:
        json.dump(linux_config, f, indent=2)
    
    print("✅ Linux配置文件已创建: config_linux.json")
    return True

def run_tests():
    """运行测试验证安装"""
    print("\n🧪 运行安装验证测试...")
    
    try:
        # 运行基础功能测试
        result = subprocess.run([sys.executable, "test_functionality.py"], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ 基础功能测试通过")
            return True
        else:
            print("❌ 基础功能测试失败")
            print(f"错误输出: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试运行失败: {e}")
        return False

def main():
    """主部署函数"""
    print("🎯 固定翼飞机投弹计算程序 - Linux部署脚本")
    print("=" * 60)
    
    steps = [
        ("检查系统环境", check_system),
        ("检查Python版本", check_python_version),
        ("安装依赖包", install_dependencies),
        ("创建服务文件", create_service_files),
        ("创建启动脚本", create_startup_script),
        ("创建Linux配置", create_config_for_linux),
        ("运行验证测试", run_tests)
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        try:
            if step_func():
                success_count += 1
                print(f"✅ {step_name} 完成")
            else:
                print(f"❌ {step_name} 失败")
        except Exception as e:
            print(f"❌ {step_name} 出现异常: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 部署结果: {success_count}/{len(steps)} 步骤成功")
    
    if success_count == len(steps):
        print("🎉 Linux部署完成！")
        print("\n📋 后续操作:")
        print("1. 将整个目录复制到Linux设备")
        print("2. 运行: ./start_bomb_release.sh")
        print("3. 或安装为系统服务: ./install_service.sh")
    else:
        print("⚠️ 部分步骤失败，请检查错误信息")
    
    return success_count == len(steps)

if __name__ == "__main__":
    main()
