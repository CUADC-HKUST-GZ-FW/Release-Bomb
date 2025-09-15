#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投弹计算服务程序
适用于Linux系统的后台服务模式
"""

import os
import sys
import time
import json
import signal
import logging
import threading
import platform
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块
from bomb_release_calculator import (
    BombReleaseCalculator, Position, SpeedData, ErrorCode
)

# 尝试导入MAVLink集成
try:
    from mavlink_integration import BombReleaseController
    MAVLINK_AVAILABLE = True
except ImportError:
    MAVLINK_AVAILABLE = False

class LinuxBombReleaseService:
    """Linux投弹计算服务"""
    
    def __init__(self, config_path: str = "config_linux.json"):
        """初始化服务"""
        self.config_path = config_path
        self.config = self.load_config()
        self.running = False
        self.controller = None
        self.last_calculation = None
        
        # 设置日志
        self.setup_logging()
        
        # 注册信号处理
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Linux投弹计算服务初始化完成")
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ 配置文件加载成功: {self.config_path}")
                return config
            else:
                print(f"⚠️ 配置文件不存在，使用默认配置: {self.config_path}")
                return self.get_default_config()
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "system": {
                "platform": "linux",
                "log_path": "/tmp/bomb_release.log",
                "pid_file": "/tmp/bomb_release.pid"
            },
            "mavlink_settings": {
                "default_connection": "/dev/ttyUSB0",
                "alternative_connections": [
                    "/dev/ttyAMA0",
                    "/dev/ttyS0",
                    "udp:127.0.0.1:14550"
                ],
                "connection_timeout": 10,
                "message_timeout": 5,
                "auto_reconnect": True,
                "reconnect_interval": 5
            }
        }
    
    def setup_logging(self):
        """设置日志系统"""
        log_path = self.config.get("system", {}).get("log_path", "/tmp/bomb_release.log")
        
        # 确保日志目录存在
        log_dir = os.path.dirname(log_path)
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def write_pid_file(self):
        """写入PID文件"""
        pid_file = self.config.get("system", {}).get("pid_file", "/tmp/bomb_release.pid")
        try:
            with open(pid_file, 'w') as f:
                f.write(str(os.getpid()))
            self.logger.info(f"PID文件写入: {pid_file}")
        except Exception as e:
            self.logger.error(f"无法写入PID文件: {e}")
    
    def remove_pid_file(self):
        """删除PID文件"""
        pid_file = self.config.get("system", {}).get("pid_file", "/tmp/bomb_release.pid")
        try:
            if os.path.exists(pid_file):
                os.remove(pid_file)
                self.logger.info(f"PID文件已删除: {pid_file}")
        except Exception as e:
            self.logger.error(f"删除PID文件失败: {e}")
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"接收到信号 {signum}，正在优雅关闭...")
        self.stop()
    
    def connect_mavlink(self) -> bool:
        """连接MAVLink"""
        if not MAVLINK_AVAILABLE:
            self.logger.error("MAVLink模块不可用")
            return False
        
        mavlink_config = self.config.get("mavlink_settings", {})
        connections = [mavlink_config.get("default_connection", "/dev/ttyUSB0")]
        connections.extend(mavlink_config.get("alternative_connections", []))
        
        for connection_string in connections:
            try:
                self.logger.info(f"尝试连接MAVLink: {connection_string}")
                self.controller = BombReleaseController(connection_string)
                
                if self.controller.connect_to_aircraft(
                    timeout=mavlink_config.get("connection_timeout", 10)
                ):
                    self.logger.info(f"✅ MAVLink连接成功: {connection_string}")
                    return True
                else:
                    self.logger.warning(f"❌ MAVLink连接失败: {connection_string}")
                    
            except Exception as e:
                self.logger.error(f"MAVLink连接异常 {connection_string}: {e}")
        
        self.logger.error("所有MAVLink连接尝试均失败")
        return False
    
    def calculate_bombing_solution(self, target_lat: float, target_lon: float, 
                                 target_alt: float = 0.0) -> Optional[Dict[str, Any]]:
        """计算投弹解决方案"""
        if not self.controller:
            self.logger.error("MAVLink控制器未初始化")
            return None
        
        try:
            target_pos = Position(target_lat, target_lon, target_alt)
            result = self.controller.calculate_bomb_release(target_pos)
            
            self.last_calculation = {
                'timestamp': time.time(),
                'target': {'lat': target_lat, 'lon': target_lon, 'alt': target_alt},
                'result': result
            }
            
            if result['success']:
                self.logger.info(
                    f"投弹计算成功: 时间={result['release_time']:.2f}s, "
                    f"距离={result['release_distance']:.0f}m"
                )
            else:
                self.logger.warning(f"投弹计算失败: {result['message']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"投弹计算异常: {e}")
            return None
    
    def monitor_connection(self):
        """监控连接状态"""
        while self.running:
            try:
                if self.controller and not self.controller.mavlink_conn.check_connection():
                    self.logger.warning("MAVLink连接断开，尝试重连...")
                    if self.config.get("mavlink_settings", {}).get("auto_reconnect", True):
                        self.connect_mavlink()
                
                time.sleep(self.config.get("mavlink_settings", {}).get("reconnect_interval", 5))
                
            except Exception as e:
                self.logger.error(f"连接监控异常: {e}")
                time.sleep(5)
    
    def run_service_loop(self):
        """服务主循环"""
        self.logger.info("投弹计算服务开始运行")
        
        # 启动连接监控线程
        monitor_thread = threading.Thread(target=self.monitor_connection, daemon=True)
        monitor_thread.start()
        
        while self.running:
            try:
                # 这里可以添加定期任务
                # 例如：健康检查、状态报告等
                
                # 简单的心跳日志
                if self.controller:
                    status = self.controller.get_status()
                    self.logger.debug(f"服务状态: 连接={status['mavlink_connected']}")
                
                time.sleep(10)  # 每10秒检查一次
                
            except Exception as e:
                self.logger.error(f"服务循环异常: {e}")
                time.sleep(5)
    
    def start(self):
        """启动服务"""
        if self.running:
            self.logger.warning("服务已在运行")
            return
        
        self.logger.info("启动投弹计算服务...")
        self.running = True
        
        # 写入PID文件
        self.write_pid_file()
        
        # 连接MAVLink
        if not self.connect_mavlink():
            self.logger.warning("MAVLink连接失败，服务将以离线模式运行")
        
        try:
            # 运行主服务循环
            self.run_service_loop()
        except KeyboardInterrupt:
            self.logger.info("接收到键盘中断信号")
        except Exception as e:
            self.logger.error(f"服务运行异常: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止服务"""
        if not self.running:
            return
        
        self.logger.info("正在停止投弹计算服务...")
        self.running = False
        
        # 清理MAVLink连接
        if self.controller:
            try:
                self.controller.cleanup()
            except Exception as e:
                self.logger.error(f"清理MAVLink连接失败: {e}")
        
        # 删除PID文件
        self.remove_pid_file()
        
        self.logger.info("投弹计算服务已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        status = {
            'running': self.running,
            'pid': os.getpid(),
            'platform': platform.system(),
            'uptime': time.time() - getattr(self, 'start_time', time.time()),
            'mavlink_available': MAVLINK_AVAILABLE,
            'controller_connected': bool(
                self.controller and 
                self.controller.mavlink_conn.is_connected
            ),
            'last_calculation': self.last_calculation
        }
        
        if self.controller:
            status.update(self.controller.get_status())
        
        return status


def create_test_target_file():
    """创建测试目标文件"""
    test_targets = {
        "targets": [
            {
                "name": "测试目标1",
                "latitude": 22.3293,
                "longitude": 114.1794,
                "altitude": 0.0,
                "description": "地面目标"
            },
            {
                "name": "测试目标2", 
                "latitude": 22.3350,
                "longitude": 114.1850,
                "altitude": 50.0,
                "description": "高台目标"
            }
        ]
    }
    
    with open("test_targets.json", 'w', encoding='utf-8') as f:
        json.dump(test_targets, f, indent=2, ensure_ascii=False)
    
    print("✅ 测试目标文件已创建: test_targets.json")


def main():
    """主函数"""
    print("🎯 Linux投弹计算服务")
    print("=" * 40)
    
    # 检查运行环境
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            # 测试模式
            print("🧪 测试模式")
            create_test_target_file()
            
            service = LinuxBombReleaseService()
            status = service.get_status()
            print(f"服务状态: {json.dumps(status, indent=2)}")
            
            return
        
        elif command == "status":
            # 状态查询
            print("📊 服务状态查询")
            service = LinuxBombReleaseService()
            status = service.get_status()
            print(json.dumps(status, indent=2))
            return
    
    # 正常服务模式
    try:
        service = LinuxBombReleaseService()
        service.start()
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
