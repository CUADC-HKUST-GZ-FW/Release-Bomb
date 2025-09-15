#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAVLink集成模块
用于安全可靠地从飞机获取飞行数据
"""

import time
import logging
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from contextlib import contextmanager

try:
    from pymavlink import mavutil
    MAVLINK_AVAILABLE = True
except ImportError:
    MAVLINK_AVAILABLE = False
    logging.warning("pymavlink库未安装，MAVLink功能将不可用")

from bomb_release_calculator import (
    BombReleaseCalculator, Position, SpeedData, 
    ErrorCode, safe_mavlink_receive
)

logger = logging.getLogger(__name__)


@dataclass
class FlightData:
    """飞行数据类"""
    position: Position
    speed: SpeedData
    timestamp: float
    altitude_msl: float = 0.0  # 海拔高度
    altitude_agl: float = 0.0  # 地面高度
    heading: float = 0.0       # 航向角(度)
    
    def is_valid(self) -> bool:
        """检查数据有效性"""
        current_time = time.time()
        # 数据不能超过5秒
        return (current_time - self.timestamp) < 5.0


class MAVLinkConnection:
    """MAVLink连接管理器"""
    
    def __init__(self, connection_string: str = "udp:127.0.0.1:14550"):
        """
        初始化MAVLink连接
        
        Args:
            connection_string: 连接字符串，默认为本地UDP连接
        """
        self.connection_string = connection_string
        self.connection = None
        self.is_connected = False
        self.last_heartbeat = 0
        
    def connect(self, timeout: float = 10.0) -> bool:
        """
        建立MAVLink连接
        
        Args:
            timeout: 连接超时时间(秒)
            
        Returns:
            是否连接成功
        """
        if not MAVLINK_AVAILABLE:
            logger.error("pymavlink库未安装，无法建立连接")
            return False
            
        try:
            logger.info(f"正在连接到 {self.connection_string}")
            self.connection = mavutil.mavlink_connection(
                self.connection_string,
                timeout=timeout
            )
            
            # 等待心跳包
            logger.info("等待飞机心跳包...")
            heartbeat = self.connection.wait_heartbeat(timeout=timeout)
            
            if heartbeat:
                self.is_connected = True
                self.last_heartbeat = time.time()
                logger.info(f"成功连接到飞机 (系统ID: {heartbeat.get_srcSystem()})")
                return True
            else:
                logger.error("未接收到心跳包，连接失败")
                return False
                
        except Exception as e:
            logger.error(f"MAVLink连接失败: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("MAVLink连接已断开")
            except Exception as e:
                logger.error(f"断开连接时出错: {e}")
            finally:
                self.connection = None
                self.is_connected = False
    
    def check_connection(self) -> bool:
        """检查连接状态"""
        if not self.is_connected or not self.connection:
            return False
        
        # 检查心跳包
        current_time = time.time()
        if current_time - self.last_heartbeat > 5.0:  # 5秒无心跳认为断线
            try:
                # 尝试接收心跳包
                heartbeat = self.connection.recv_match(
                    type='HEARTBEAT', 
                    blocking=False
                )
                if heartbeat:
                    self.last_heartbeat = current_time
                    return True
                else:
                    logger.warning("连接可能已断开，未收到心跳包")
                    return False
            except Exception as e:
                logger.error(f"检查连接状态时出错: {e}")
                return False
        
        return True
    
    @contextmanager
    def safe_connection(self):
        """安全连接上下文管理器"""
        try:
            if not self.is_connected:
                if not self.connect():
                    raise ConnectionError("无法建立MAVLink连接")
            yield self
        finally:
            # 可选择是否自动断开，这里保持连接以提高效率
            pass


class FlightDataCollector:
    """飞行数据收集器"""
    
    def __init__(self, mavlink_conn: MAVLinkConnection):
        """
        初始化数据收集器
        
        Args:
            mavlink_conn: MAVLink连接对象
        """
        self.mavlink_conn = mavlink_conn
        self.calculator = BombReleaseCalculator()
        
    def get_speed_data(self, timeout: float = 5.0) -> Optional[SpeedData]:
        """
        获取速度数据 (空速和地速)
        
        Args:
            timeout: 超时时间(秒)
            
        Returns:
            SpeedData对象或None
        """
        if not self.mavlink_conn.check_connection():
            logger.error("MAVLink连接未建立或已断开")
            return None
        
        try:
            # 获取VFR_HUD消息，包含空速和地速
            msg = safe_mavlink_receive(
                self.mavlink_conn.connection, 
                'VFR_HUD', 
                timeout
            )
            
            if msg is None:
                logger.error("未能接收到VFR_HUD消息")
                return None
            
            airspeed = msg.airspeed
            groundspeed = msg.groundspeed
            
            # 验证数据
            is_valid, error_msg = self.calculator.validate_mavlink_data(
                airspeed, groundspeed
            )
            
            if not is_valid:
                logger.error(f"速度数据验证失败: {error_msg}")
                return None
            
            return SpeedData(airspeed=airspeed, groundspeed=groundspeed)
            
        except Exception as e:
            logger.error(f"获取速度数据时出错: {e}")
            return None
    
    def get_position_data(self, timeout: float = 5.0) -> Optional[Position]:
        """
        获取位置数据
        
        Args:
            timeout: 超时时间(秒)
            
        Returns:
            Position对象或None
        """
        if not self.mavlink_conn.check_connection():
            logger.error("MAVLink连接未建立或已断开")
            return None
        
        try:
            # 获取GLOBAL_POSITION_INT消息
            msg = safe_mavlink_receive(
                self.mavlink_conn.connection,
                'GLOBAL_POSITION_INT',
                timeout
            )
            
            if msg is None:
                logger.error("未能接收到GLOBAL_POSITION_INT消息")
                return None
            
            # 转换单位（消息中的坐标是1e7缩放的）
            latitude = msg.lat / 1e7
            longitude = msg.lon / 1e7
            altitude = msg.alt / 1000.0  # 毫米转米
            
            return Position(
                latitude=latitude,
                longitude=longitude,
                altitude=altitude
            )
            
        except Exception as e:
            logger.error(f"获取位置数据时出错: {e}")
            return None
    
    def get_complete_flight_data(self, timeout: float = 10.0) -> Optional[FlightData]:
        """
        获取完整的飞行数据
        
        Args:
            timeout: 总超时时间(秒)
            
        Returns:
            FlightData对象或None
        """
        start_time = time.time()
        half_timeout = timeout / 2
        
        try:
            # 获取位置数据
            position = self.get_position_data(half_timeout)
            if position is None:
                logger.error("无法获取位置数据")
                return None
            
            # 检查剩余时间
            elapsed = time.time() - start_time
            remaining_timeout = timeout - elapsed
            if remaining_timeout <= 0:
                logger.error("获取位置数据超时")
                return None
            
            # 获取速度数据
            speed = self.get_speed_data(remaining_timeout)
            if speed is None:
                logger.error("无法获取速度数据")
                return None
            
            return FlightData(
                position=position,
                speed=speed,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"获取完整飞行数据时出错: {e}")
            return None


class BombReleaseController:
    """投弹控制器 - 整合所有功能"""
    
    def __init__(self, connection_string: str = "udp:127.0.0.1:14550"):
        """
        初始化投弹控制器
        
        Args:
            connection_string: MAVLink连接字符串
        """
        self.mavlink_conn = MAVLinkConnection(connection_string)
        self.data_collector = FlightDataCollector(self.mavlink_conn)
        self.calculator = BombReleaseCalculator()
        self.last_calculation = None
        self.calculation_history = []
        
    def connect_to_aircraft(self, timeout: float = 10.0) -> bool:
        """
        连接到飞机
        
        Args:
            timeout: 连接超时时间(秒)
            
        Returns:
            是否连接成功
        """
        return self.mavlink_conn.connect(timeout)
    
    def calculate_bomb_release(self, target_pos: Position) -> Dict[str, Any]:
        """
        计算投弹参数（主要接口）
        
        Args:
            target_pos: 目标位置
            
        Returns:
            计算结果字典
        """
        result = {
            'success': False,
            'error_code': ErrorCode.CALCULATION_ERROR,
            'message': '',
            'timestamp': time.time()
        }
        
        try:
            # 检查连接
            if not self.mavlink_conn.check_connection():
                result.update({
                    'error_code': ErrorCode.CALCULATION_ERROR,
                    'message': 'MAVLink连接未建立或已断开'
                })
                return result
            
            # 获取当前飞行数据
            flight_data = self.data_collector.get_complete_flight_data()
            if flight_data is None:
                result.update({
                    'error_code': ErrorCode.CALCULATION_ERROR,
                    'message': '无法获取当前飞行数据'
                })
                return result
            
            # 检查数据有效性
            if not flight_data.is_valid():
                result.update({
                    'error_code': ErrorCode.CALCULATION_ERROR,
                    'message': '飞行数据已过期，请重新获取'
                })
                return result
            
            # 执行投弹计算
            calc_result = self.calculator.calculate_release_point(
                flight_data.position,
                target_pos,
                flight_data.speed
            )
            
            # 保存计算历史
            self.last_calculation = calc_result
            self.calculation_history.append({
                'timestamp': time.time(),
                'flight_data': flight_data,
                'target_pos': target_pos,
                'result': calc_result
            })
            
            # 保持最近10次计算记录
            if len(self.calculation_history) > 10:
                self.calculation_history.pop(0)
            
            return calc_result
            
        except Exception as e:
            logger.error(f"投弹计算过程出错: {e}")
            result.update({
                'error_code': ErrorCode.CALCULATION_ERROR,
                'message': f'计算过程出现错误: {str(e)}'
            })
            return result
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            状态信息字典
        """
        return {
            'mavlink_connected': self.mavlink_conn.is_connected,
            'connection_string': self.mavlink_conn.connection_string,
            'last_heartbeat': self.mavlink_conn.last_heartbeat,
            'calculation_count': len(self.calculation_history),
            'last_calculation_time': (
                self.last_calculation.get('timestamp') 
                if self.last_calculation else None
            )
        }
    
    def cleanup(self):
        """清理资源"""
        self.mavlink_conn.disconnect()
        logger.info("投弹控制器已清理资源")


def main_integration_example():
    """完整集成示例"""
    print("🎯 MAVLink集成投弹计算示例")
    print("=" * 50)
    
    # 创建控制器
    controller = BombReleaseController()
    
    try:
        # 连接到飞机（示例中使用模拟连接）
        print("正在连接到飞机...")
        if controller.connect_to_aircraft(timeout=5.0):
            print("✅ 成功连接到飞机")
            
            # 设置目标位置
            target = Position(
                latitude=22.3293,
                longitude=114.1794,
                altitude=0.0
            )
            
            # 计算投弹参数
            print("正在计算投弹参数...")
            result = controller.calculate_bomb_release(target)
            
            if result['success']:
                print(f"✅ 投弹计算成功!")
                print(f"📍 投弹时间: {result['release_time']:.2f} 秒")
                print(f"📏 投弹距离: {result['release_distance']:.0f} 米")
                print(f"⏱️ 弹药飞行时间: {result['flight_time']:.2f} 秒")
            else:
                print(f"❌ 投弹计算失败: {result['message']}")
        else:
            print("❌ 无法连接到飞机（这在示例中是正常的）")
            
    except Exception as e:
        print(f"程序执行出错: {e}")
    finally:
        controller.cleanup()


if __name__ == "__main__":
    main_integration_example()
