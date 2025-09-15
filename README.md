# 固定翼飞机投弹时刻计算程序

一个稳定性和容错性优先的Python程序，用于计算固定翼飞机投弹的最佳时刻。

## 🎯 功能特性

- **高精度计算**: 基于抛物线轨迹和地球几何学的精确投弹时刻计算
- **MAVLink集成**: 直接从飞机获取实时飞行数据（空速、地速、位置）
- **稳定性优先**: 完整的错误处理、输入验证和数值稳定性保证
- **容错设计**: 网络断线重连、数据验证、异常恢复
- **详细日志**: 完整的操作日志和计算历史记录

## 📋 系统要求

- Python 3.7+
- pymavlink 2.4.0+
- numpy 1.21.0+

## 🚀 Linux系统部署

### 自动部署（推荐）

1. **下载程序到Linux设备**
```bash
# 复制整个ReleaseBomb目录到Linux设备
scp -r ReleaseBomb/ user@linux-device:/home/user/
```

2. **运行自动部署脚本**
```bash
cd ReleaseBomb
chmod +x deploy_linux.sh
./deploy_linux.sh
```

3. **安装为系统服务（可选）**
```bash
./deploy_linux.sh --service
```

### 手动部署

1. **检查Python环境**
```bash
python3 --version  # 需要Python 3.7+
pip3 --version
```

2. **安装依赖**
```bash
pip3 install -r requirements.txt
```

3. **设置串口权限**
```bash
sudo usermod -a -G dialout $USER
# 重新登录生效
```

4. **运行程序**
```bash
# 交互式运行
python3 quick_bomb_calc.py

# 服务模式
python3 bomb_release_service.py

# 后台运行
nohup python3 bomb_release_service.py > /dev/null 2>&1 &
```

### Linux配置说明

Linux系统使用专门的配置文件 `config_linux.json`：

```json
{
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
    "auto_reconnect": true,
    "reconnect_interval": 5
  }
}
```

### 常见Linux串口设备

| 设备 | 说明 |
|------|------|
| /dev/ttyUSB0 | USB转串口设备 |
| /dev/ttyAMA0 | 树莓派硬件串口 |
| /dev/ttyS0 | 标准串口 |
| /dev/ttyACM0 | USB CDC设备 |

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 基础使用（不需要MAVLink连接）

```python
from bomb_release_calculator import BombReleaseCalculator, Position, SpeedData

# 创建计算器
calculator = BombReleaseCalculator()

# 设置飞机位置
aircraft_pos = Position(
    latitude=22.3193,    # 纬度
    longitude=114.1694,  # 经度
    altitude=500.0       # 高度(米)
)

# 设置目标位置
target_pos = Position(
    latitude=22.3293,
    longitude=114.1794,
    altitude=0.0
)

# 设置速度数据
speed_data = SpeedData(
    airspeed=50.0,      # 空速 m/s
    groundspeed=45.0    # 地速 m/s
)

# 计算投弹参数
result = calculator.calculate_release_point(aircraft_pos, target_pos, speed_data)

if result['success']:
    print(f"投弹倒计时: {result['release_time']:.2f} 秒")
    print(f"投弹距离: {result['release_distance']:.0f} 米")
    print(f"飞行时间: {result['flight_time']:.2f} 秒")
else:
    print(f"计算失败: {result['message']}")
```

### 3. MAVLink集成使用

```python
from mavlink_integration import BombReleaseController

# 创建控制器
controller = BombReleaseController("udp:127.0.0.1:14550")

# 连接到飞机
if controller.connect_to_aircraft():
    # 设置目标
    target = Position(latitude=22.3293, longitude=114.1794, altitude=0.0)
    
    # 计算投弹参数（自动获取当前飞行数据）
    result = controller.calculate_bomb_release(target)
    
    if result['success']:
        print(f"投弹倒计时: {result['release_time']:.2f} 秒")
    else:
        print(f"计算失败: {result['message']}")
    
    controller.cleanup()
```

### 4. 运行示例程序

```bash
python example_usage.py
```

## 📁 文件结构

```
ReleaseBomb/
├── bomb_release_calculator.py  # 核心计算模块
├── mavlink_integration.py      # MAVLink集成模块
├── example_usage.py            # 使用示例
├── quick_bomb_calc.py          # 快速计算脚本
├── bomb_release_service.py     # Linux服务程序
├── platform_compat.py         # 跨平台兼容性工具
├── test_functionality.py      # 功能测试脚本
├── deploy_linux.py            # Linux部署脚本(Python)
├── deploy_linux.sh            # Linux部署脚本(Shell)
├── requirements.txt           # 依赖包列表
├── config.json               # Windows配置文件
├── config_linux.json         # Linux配置文件
└── README.md                 # 说明文档
```

## 🔧 配置说明

### 炸弹参数配置

程序默认配置为350ml圆柱形矿泉水瓶：

```python
BombCharacteristics(
    mass=0.35,              # 质量 350g
    drag_coefficient=0.47,   # 圆柱体阻力系数
    cross_sectional_area=0.003  # 横截面积 m²
)
```

### MAVLink连接配置

支持多种连接方式：

```python
# UDP连接（默认）
"udp:127.0.0.1:14550"

# 串口连接
"COM3"  # Windows
"/dev/ttyUSB0"  # Linux

# TCP连接
"tcp:192.168.1.100:5760"
```

## 📊 输入参数说明

### 必需参数

| 参数 | 类型 | 说明 | 单位 |
|------|------|------|------|
| aircraft_latitude | float | 飞机纬度 | 度 |
| aircraft_longitude | float | 飞机经度 | 度 |
| aircraft_altitude | float | 飞机高度 | 米 |
| target_latitude | float | 目标纬度 | 度 |
| target_longitude | float | 目标经度 | 度 |
| target_altitude | float | 目标高度 | 米 |
| airspeed | float | 空速 | m/s |
| groundspeed | float | 地速 | m/s |

### MAVLink数据获取

```python
# 通过pymavlink获取空速和地速
msg = connection.recv_match(type='VFR_HUD', blocking=True, timeout=5)
airspeed = msg.airspeed      # m/s
groundspeed = msg.groundspeed # m/s

# 获取位置数据
msg = connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=5)
latitude = msg.lat / 1e7     # 度
longitude = msg.lon / 1e7    # 度
altitude = msg.alt / 1000.0  # 米
```

## 📈 输出结果说明

### 成功结果

```python
{
    'success': True,
    'release_time': 12.45,      # 投弹倒计时(秒)
    'release_distance': 560.0,  # 提前投弹距离(米)
    'flight_time': 8.2,         # 弹药飞行时间(秒)
    'wind_speed': 5.0,          # 风速影响(m/s)
    'calculations': {
        'target_distance': 1200.0,    # 目标总距离(米)
        'target_bearing': 45.2,       # 目标方位角(度)
        'altitude_difference': 500.0  # 高度差(米)
    }
}
```

### 失败结果

```python
{
    'success': False,
    'error_code': ErrorCode.INVALID_COORDINATES,
    'message': '飞机高度过低: 30m，最小高度: 50m'
}
```

## ⚠️ 安全注意事项

1. **高度限制**: 最小投弹高度50米
2. **距离限制**: 最大投弹距离50公里
3. **速度验证**: 自动验证空速和地速的合理性
4. **数据时效**: 飞行数据有效期5秒
5. **连接监控**: 自动监控MAVLink连接状态

## 🔍 错误代码说明

| 错误代码 | 说明 |
|----------|------|
| SUCCESS | 计算成功 |
| INVALID_COORDINATES | 无效坐标 |
| INVALID_SPEED | 无效速度 |
| TARGET_TOO_FAR | 目标距离过远 |
| CALCULATION_ERROR | 计算错误 |
| NUMERICAL_INSTABILITY | 数值不稳定 |

## 📝 日志记录

程序会自动记录所有操作到 `bomb_release.log` 文件：

```
2024-01-15 10:30:25 - INFO - 投弹计算成功: 投弹时间=12.45s, 投弹距离=560m
2024-01-15 10:30:30 - ERROR - 飞机高度过低: 30m，最小高度: 50m
2024-01-15 10:30:35 - WARNING - 空速(60)和地速(30)差异较大，请检查数据
```

## 🧪 测试

运行完整测试：

```bash
python example_usage.py
```

测试内容包括：
- 基础计算功能
- MAVLink数据模拟
- 错误处理机制
- 真实MAVLink连接（如果可用）

## 🤝 贡献

欢迎提交Issue和Pull Request来改进程序！

## 📄 许可证

MIT License

## 📞 技术支持

如有问题，请查看日志文件或联系技术支持团队。

---

**⚠️ 重要提醒**: 本程序仅用于竞赛和教学目的，实际应用时请遵守相关法律法规！
