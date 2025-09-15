#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
固定翼飞机投弹时刻计算程序
稳定性和容错性优先设计

功能：根据飞机当前位置、目标位置、空速和地速计算投弹时刻
考虑因素：抛物线运动、地球曲率、风速影响、重力加速度
"""

import math
import logging
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bomb_release.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """错误代码枚举"""
    SUCCESS = 0
    INVALID_COORDINATES = 1
    INVALID_SPEED = 2
    TARGET_TOO_FAR = 3
    CALCULATION_ERROR = 4
    NUMERICAL_INSTABILITY = 5


@dataclass
class Position:
    """位置坐标类"""
    latitude: float   # 纬度 (度)
    longitude: float  # 经度 (度)
    altitude: float = 0.0  # 高度 (米)
    
    def __post_init__(self):
        """验证坐标有效性"""
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"无效纬度: {self.latitude}, 必须在-90到90度之间")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"无效经度: {self.longitude}, 必须在-180到180度之间")
        if self.altitude < 0:
            raise ValueError(f"无效高度: {self.altitude}, 不能为负数")


@dataclass
class SpeedData:
    """速度数据类"""
    airspeed: float    # 空速 (m/s)
    groundspeed: float # 地速 (m/s)
    
    def __post_init__(self):
        """验证速度有效性"""
        if self.airspeed <= 0:
            raise ValueError(f"无效空速: {self.airspeed}, 必须大于0")
        if self.groundspeed <= 0:
            raise ValueError(f"无效地速: {self.groundspeed}, 必须大于0")
        
        # 检查速度合理性（空速和地速差异不应过大）
        speed_ratio = abs(self.airspeed - self.groundspeed) / max(self.airspeed, self.groundspeed)
        if speed_ratio > 0.5:  # 50%的差异阈值
            logger.warning(f"空速({self.airspeed})和地速({self.groundspeed})差异较大，请检查数据")


@dataclass
class BombCharacteristics:
    """炸弹特性类"""
    mass: float = 0.35  # 质量 (kg) - 350ml矿泉水
    drag_coefficient: float = 0.47  # 阻力系数 (圆柱体)
    cross_sectional_area: float = 0.003  # 横截面积 (m²)
    
    def __post_init__(self):
        """验证炸弹参数"""
        if self.mass <= 0:
            raise ValueError(f"无效质量: {self.mass}")
        if self.drag_coefficient <= 0:
            raise ValueError(f"无效阻力系数: {self.drag_coefficient}")
        if self.cross_sectional_area <= 0:
            raise ValueError(f"无效横截面积: {self.cross_sectional_area}")


class BombReleaseCalculator:
    """投弹时刻计算器"""
    
    # 常数定义
    EARTH_RADIUS = 6371000.0  # 地球半径 (米)
    GRAVITY = 9.81  # 重力加速度 (m/s²)
    AIR_DENSITY = 1.225  # 空气密度 (kg/m³) - 海平面标准
    
    # 数值计算参数
    MAX_ITERATIONS = 1000
    CONVERGENCE_TOLERANCE = 1e-6
    MAX_REASONABLE_DISTANCE = 50000.0  # 最大合理距离 (米)
    MIN_RELEASE_HEIGHT = 50.0  # 最小投弹高度 (米)
    
    def __init__(self):
        """初始化计算器"""
        self.bomb_characteristics = BombCharacteristics()
        
    def calculate_distance_and_bearing(self, pos1: Position, pos2: Position) -> Tuple[float, float]:
        """
        计算两点间距离和方位角（使用Haversine公式）
        
        Args:
            pos1: 起始位置
            pos2: 目标位置
            
        Returns:
            Tuple[距离(米), 方位角(弧度)]
        """
        try:
            # 转换为弧度
            lat1_rad = math.radians(pos1.latitude)
            lon1_rad = math.radians(pos1.longitude)
            lat2_rad = math.radians(pos2.latitude)
            lon2_rad = math.radians(pos2.longitude)
            
            # Haversine公式计算距离
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            
            a = (math.sin(dlat/2)**2 + 
                 math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
            
            # 数值稳定性检查
            if a > 1.0:
                a = 1.0
            elif a < 0.0:
                a = 0.0
                
            c = 2 * math.asin(math.sqrt(a))
            distance = self.EARTH_RADIUS * c
            
            # 计算方位角
            y = math.sin(dlon) * math.cos(lat2_rad)
            x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
                 math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon))
            bearing = math.atan2(y, x)
            
            return distance, bearing
            
        except Exception as e:
            logger.error(f"距离和方位角计算错误: {e}")
            raise ValueError(f"无法计算距离和方位角: {e}")
    
    def calculate_wind_effect(self, airspeed: float, groundspeed: float, 
                            bearing: float) -> Tuple[float, float]:
        """
        计算风速影响
        
        Args:
            airspeed: 空速 (m/s)
            groundspeed: 地速 (m/s)
            bearing: 飞行方位角 (弧度)
            
        Returns:
            Tuple[风速(m/s), 风向与航向夹角(弧度)]
        """
        try:
            # 使用向量分解计算风速
            wind_speed = math.sqrt(airspeed**2 + groundspeed**2 - 
                                 2 * airspeed * groundspeed * math.cos(0))
            
            # 简化处理：假设风速为空速和地速的差值
            wind_speed = abs(airspeed - groundspeed)
            
            # 风向角估算（简化模型）
            if airspeed > groundspeed:
                wind_angle = math.pi  # 逆风
            else:
                wind_angle = 0  # 顺风
                
            return wind_speed, wind_angle
            
        except Exception as e:
            logger.error(f"风速计算错误: {e}")
            return 0.0, 0.0  # 返回安全默认值
    
    def calculate_ballistic_trajectory(self, initial_velocity: float, 
                                     height: float, distance: float,
                                     wind_speed: float = 0.0) -> Optional[float]:
        """
        计算弹道轨迹飞行时间（简化但稳定的模型）
        
        Args:
            initial_velocity: 初始速度 (m/s)
            height: 投弹高度 (米)
            distance: 水平距离 (米)
            wind_speed: 风速 (m/s)
            
        Returns:
            飞行时间 (秒) 或 None (无解)
        """
        try:
            if height <= 0:
                logger.error(f"无效投弹高度: {height}")
                return None
                
            if distance <= 0:
                logger.error(f"无效水平距离: {distance}")
                return None
            
            # 使用简化的抛物线运动模型（更稳定可靠）
            # 垂直方向：h = 0.5 * g * t²
            # 水平方向：d = v * t
            
            # 计算垂直下落时间
            vertical_time = math.sqrt(2 * height / self.GRAVITY)
            
            # 考虑风速影响的有效水平速度
            effective_horizontal_velocity = initial_velocity + wind_speed
            
            if abs(effective_horizontal_velocity) < 1e-10:
                logger.error("有效水平速度接近零，无法到达目标")
                return None
            
            # 计算到达目标所需的水平飞行时间
            horizontal_time = distance / abs(effective_horizontal_velocity)
            
            # 检查物理合理性：水平飞行时间不能超过垂直下落时间太多
            if horizontal_time > vertical_time * 1.2:  # 允许20%的误差
                logger.warning(f"水平飞行时间({horizontal_time:.2f}s)超出垂直下落时间({vertical_time:.2f}s)")
                # 使用垂直下落时间作为飞行时间
                flight_time = vertical_time
            else:
                # 使用较大的时间（确保弹药能够下落到目标高度）
                flight_time = max(horizontal_time, vertical_time * 0.8)
            
            # 最终合理性检查
            if flight_time <= 0 or flight_time > 60:
                logger.error(f"飞行时间不合理: {flight_time}")
                return None
            
            # 考虑简单的空气阻力修正（增加10%的时间）
            flight_time *= 1.1
            
            return flight_time
            
        except Exception as e:
            logger.error(f"弹道轨迹计算错误: {e}")
            return None
    
    def calculate_release_point(self, aircraft_pos: Position, target_pos: Position,
                              speed_data: SpeedData) -> Dict[str, Any]:
        """
        计算投弹时刻和位置
        
        Args:
            aircraft_pos: 飞机当前位置
            target_pos: 目标位置
            speed_data: 速度数据
            
        Returns:
            计算结果字典
        """
        result = {
            'success': False,
            'error_code': ErrorCode.SUCCESS,
            'message': '',
            'release_time': None,
            'release_distance': None,
            'flight_time': None,
            'wind_speed': None,
            'calculations': {}
        }
        
        try:
            # 输入验证
            if aircraft_pos.altitude < self.MIN_RELEASE_HEIGHT:
                result.update({
                    'error_code': ErrorCode.INVALID_COORDINATES,
                    'message': f'飞机高度过低: {aircraft_pos.altitude}m，最小高度: {self.MIN_RELEASE_HEIGHT}m'
                })
                return result
            
            # 计算距离和方位角
            distance, bearing = self.calculate_distance_and_bearing(aircraft_pos, target_pos)
            
            if distance > self.MAX_REASONABLE_DISTANCE:
                result.update({
                    'error_code': ErrorCode.TARGET_TOO_FAR,
                    'message': f'目标距离过远: {distance:.0f}m，最大距离: {self.MAX_REASONABLE_DISTANCE}m'
                })
                return result
            
            # 计算风速影响
            wind_speed, wind_angle = self.calculate_wind_effect(
                speed_data.airspeed, speed_data.groundspeed, bearing
            )
            
            # 计算弹道飞行时间
            flight_time = self.calculate_ballistic_trajectory(
                speed_data.groundspeed,
                aircraft_pos.altitude - target_pos.altitude,
                distance,
                wind_speed
            )
            
            if flight_time is None:
                result.update({
                    'error_code': ErrorCode.CALCULATION_ERROR,
                    'message': '无法计算有效的弹道轨迹'
                })
                return result
            
            # 计算提前投弹距离
            release_distance = speed_data.groundspeed * flight_time
            
            # 安全性检查
            if release_distance > distance * 2:
                result.update({
                    'error_code': ErrorCode.NUMERICAL_INSTABILITY,
                    'message': f'计算结果不稳定，投弹距离({release_distance:.0f}m)过大'
                })
                return result
            
            # 计算投弹时间（到达投弹点的时间）
            release_time = (distance - release_distance) / speed_data.groundspeed
            
            if release_time < 0:
                result.update({
                    'error_code': ErrorCode.CALCULATION_ERROR,
                    'message': '已经错过最佳投弹时机，需要重新规划航线'
                })
                return result
            
            # 成功结果
            result.update({
                'success': True,
                'release_time': release_time,
                'release_distance': release_distance,
                'flight_time': flight_time,
                'wind_speed': wind_speed,
                'calculations': {
                    'target_distance': distance,
                    'target_bearing': math.degrees(bearing),
                    'wind_angle': math.degrees(wind_angle),
                    'aircraft_altitude': aircraft_pos.altitude,
                    'target_altitude': target_pos.altitude,
                    'altitude_difference': aircraft_pos.altitude - target_pos.altitude
                }
            })
            
            logger.info(f"投弹计算成功: 投弹时间={release_time:.2f}s, 投弹距离={release_distance:.0f}m")
            
        except Exception as e:
            logger.error(f"投弹计算错误: {e}")
            result.update({
                'error_code': ErrorCode.CALCULATION_ERROR,
                'message': f'计算过程出现错误: {str(e)}'
            })
        
        return result
    
    def validate_mavlink_data(self, airspeed: Optional[float], 
                            groundspeed: Optional[float]) -> Tuple[bool, str]:
        """
        验证MAVLink数据有效性
        
        Args:
            airspeed: 空速数据
            groundspeed: 地速数据
            
        Returns:
            Tuple[是否有效, 错误信息]
        """
        if airspeed is None:
            return False, "无法获取空速数据"
        
        if groundspeed is None:
            return False, "无法获取地速数据"
        
        if airspeed <= 0:
            return False, f"无效空速值: {airspeed}"
        
        if groundspeed <= 0:
            return False, f"无效地速值: {groundspeed}"
        
        # 合理性检查
        if airspeed > 200:  # 200 m/s = 720 km/h
            return False, f"空速过高，可能有误: {airspeed} m/s"
        
        if groundspeed > 200:
            return False, f"地速过高，可能有误: {groundspeed} m/s"
        
        return True, ""


def safe_mavlink_receive(connection, msg_type: str, timeout: float = 5.0) -> Optional[Any]:
    """
    安全接收MAVLink消息
    
    Args:
        connection: MAVLink连接对象
        msg_type: 消息类型
        timeout: 超时时间(秒)
        
    Returns:
        消息对象或None
    """
    try:
        msg = connection.recv_match(type=msg_type, blocking=True, timeout=timeout)
        return msg
    except Exception as e:
        logger.error(f"接收MAVLink消息失败 ({msg_type}): {e}")
        return None


def main_calculation_example():
    """主要计算示例"""
    try:
        # 创建计算器实例
        calculator = BombReleaseCalculator()
        
        # 示例数据
        aircraft_pos = Position(
            latitude=22.3193,    # 深圳纬度
            longitude=114.1694,  # 深圳经度
            altitude=500.0       # 高度500米
        )
        
        target_pos = Position(
            latitude=22.3293,    # 目标纬度
            longitude=114.1794,  # 目标经度
            altitude=0.0         # 目标高度（地面）
        )
        
        speed_data = SpeedData(
            airspeed=50.0,      # 空速50 m/s
            groundspeed=45.0    # 地速45 m/s
        )
        
        # 计算投弹参数
        result = calculator.calculate_release_point(aircraft_pos, target_pos, speed_data)
        
        # 输出结果
        if result['success']:
            print(f"✅ 投弹计算成功!")
            print(f"📍 投弹时间: {result['release_time']:.2f} 秒")
            print(f"📏 投弹距离: {result['release_distance']:.0f} 米")
            print(f"⏱️ 弹药飞行时间: {result['flight_time']:.2f} 秒")
            print(f"💨 风速影响: {result['wind_speed']:.1f} m/s")
            print(f"📊 计算详情: {result['calculations']}")
        else:
            print(f"❌ 投弹计算失败!")
            print(f"错误代码: {result['error_code']}")
            print(f"错误信息: {result['message']}")
            
    except Exception as e:
        logger.error(f"主程序执行错误: {e}")
        print(f"程序执行出现错误: {e}")


if __name__ == "__main__":
    print("🎯 固定翼飞机投弹时刻计算程序")
    print("=" * 50)
    main_calculation_example()
