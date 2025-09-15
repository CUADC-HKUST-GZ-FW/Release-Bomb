# 固定翼飞机投弹计算程序 - 部署指南

## 📋 程序概述

本程序是一个专为固定翼飞机设计的投弹时刻计算系统，具备以下特点：

- **高稳定性**: 完整的错误处理和异常恢复机制
- **高容错性**: 网络断线重连、数据验证、输入校验
- **跨平台**: 支持Windows调试和Linux实际部署
- **实时性**: 直接从MAVLink获取飞行数据进行计算

## 🎯 核心功能

### 1. 投弹时刻计算
- 根据飞机当前位置、目标位置、飞行速度计算最佳投弹时刻
- 考虑抛物线运动、风速影响、重力加速度等物理因素
- 输出投弹倒计时时间和提前距离

### 2. MAVLink集成
- 自动从飞机飞控系统获取实时数据：
  - 空速 (airspeed)
  - 地速 (groundspeed) 
  - 位置坐标 (GPS)
  - 高度信息
- 支持多种连接方式：串口、UDP、TCP

### 3. 安全保障
- 最小投弹高度限制 (50米)
- 最大目标距离限制 (50公里)
- 速度数据合理性检查
- 实时连接状态监控

## 🖥️ 系统要求

### 硬件要求
- **CPU**: ARM或x86架构
- **内存**: 最小512MB
- **存储**: 最小100MB可用空间
- **串口**: 用于MAVLink通信（可选USB转串口）

### 软件要求
- **操作系统**: Linux (推荐Ubuntu 18.04+)
- **Python**: 3.7或更高版本
- **依赖包**: pymavlink, numpy

### 网络要求
- 支持MAVLink UDP连接 (可选)
- 用于远程监控和日志查看

## 🚀 Windows调试环境

### 快速开始
```bash
# 1. 下载程序
git clone <repository> ReleaseBomb
cd ReleaseBomb

# 2. 安装依赖 (可选，基础功能无需MAVLink)
pip install -r requirements.txt

# 3. 运行测试
python test_functionality.py

# 4. 使用示例
python example_usage.py

# 5. 快速计算
python quick_bomb_calc.py
```

### 开发测试
- 使用模拟数据进行算法验证
- 测试各种边界条件和异常情况
- 验证跨平台兼容性

## 🐧 Linux生产环境

### 自动部署 (推荐)
```bash
# 1. 上传到Linux设备
scp -r ReleaseBomb/ pi@raspberrypi:/home/pi/

# 2. SSH登录设备
ssh pi@raspberrypi

# 3. 进入目录
cd ReleaseBomb

# 4. 运行部署脚本
chmod +x deploy_linux.sh
./deploy_linux.sh

# 5. 安装系统服务 (可选)
./deploy_linux.sh --service
```

### 手动部署
```bash
# 1. 检查环境
python3 --version
pip3 --version

# 2. 安装依赖
pip3 install -r requirements.txt

# 3. 设置权限
sudo usermod -a -G dialout $USER
chmod +x *.py *.sh

# 4. 创建配置
python3 platform_compat.py

# 5. 运行测试
python3 test_functionality.py
```

## 📱 使用方式

### 1. 命令行模式
```bash
# 直接指定参数
python3 quick_bomb_calc.py 22.3193 114.1694 500 22.3293 114.1794 0 50 45

# 交互式输入
python3 quick_bomb_calc.py
# 选择模式1，然后输入各项参数
```

### 2. 服务模式 (推荐)
```bash
# 前台运行
python3 bomb_release_service.py

# 后台运行
nohup python3 bomb_release_service.py > /dev/null 2>&1 &

# 系统服务
sudo systemctl start bomb-release
sudo systemctl status bomb-release
```

### 3. API调用模式
```python
from bomb_release_calculator import BombReleaseCalculator, Position, SpeedData

calculator = BombReleaseCalculator()
result = calculator.calculate_release_point(aircraft_pos, target_pos, speed_data)

if result['success']:
    print(f"投弹倒计时: {result['release_time']:.2f} 秒")
```

## 🔌 硬件连接

### 串口连接 (推荐)
```
飞控 ↔ 串口线 ↔ Linux设备
TELEM2   USB转串口   /dev/ttyUSB0
```

### 网络连接
```
飞控 ↔ 数传 ↔ 地面站 ↔ Linux设备
     915MHz    UDP:14550
```

### 常见设备路径
- 树莓派: `/dev/ttyAMA0`, `/dev/ttyS0`
- USB设备: `/dev/ttyUSB0`, `/dev/ttyUSB1`
- 其他: `/dev/ttyACM0`

## 📊 输入输出

### 输入参数
| 参数 | 类型 | 单位 | 获取方式 |
|------|------|------|----------|
| 飞机纬度 | float | 度 | GPS/MAVLink |
| 飞机经度 | float | 度 | GPS/MAVLink |
| 飞机高度 | float | 米 | 气压计/MAVLink |
| 目标纬度 | float | 度 | 任务规划/用户输入 |
| 目标经度 | float | 度 | 任务规划/用户输入 |
| 目标高度 | float | 米 | 地形数据/用户输入 |
| 空速 | float | m/s | 空速计/MAVLink |
| 地速 | float | m/s | GPS/MAVLink |

### 输出结果
| 参数 | 说明 | 单位 |
|------|------|------|
| release_time | 投弹倒计时 | 秒 |
| release_distance | 提前投弹距离 | 米 |
| flight_time | 弹药飞行时间 | 秒 |
| wind_speed | 风速影响 | m/s |

### 使用示例
```
输入:
  飞机: 22.3193°N, 114.1694°E, 500m
  目标: 22.3293°N, 114.1794°E, 0m
  速度: 空速50m/s, 地速45m/s

输出:
  ✅ 计算成功!
  📍 投弹倒计时: 22.56 秒
  📏 提前距离: 500 米
  🎯 飞行时间: 11.11 秒
  💨 风速影响: 5.0 m/s
```

## 🛠️ 故障排除

### 常见问题

**1. MAVLink连接失败**
```bash
# 检查串口设备
ls -l /dev/tty*

# 检查权限
groups $USER | grep dialout

# 测试串口
sudo minicom -D /dev/ttyUSB0 -b 57600
```

**2. Python依赖问题**
```bash
# 检查Python版本
python3 --version

# 安装依赖
pip3 install pymavlink numpy

# 虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. 权限问题**
```bash
# 添加用户到dialout组
sudo usermod -a -G dialout $USER

# 设置文件权限
chmod +x *.py *.sh

# 检查文件所有者
ls -la
```

**4. 计算结果异常**
- 检查输入数据合理性
- 确认飞机高度满足最低要求 (50m)
- 验证目标距离在有效范围内 (50km)
- 查看日志文件了解详细错误信息

### 日志查看
```bash
# 实时日志
tail -f /tmp/bomb_release.log

# 系统服务日志
journalctl -u bomb-release -f

# 程序日志
cat bomb_release.log
```

## 📈 性能优化

### Linux优化建议
1. **关闭不必要服务**: 减少系统负载
2. **设置CPU调度**: 提高实时性
3. **优化内存**: 使用swap分区
4. **网络优化**: 降低延迟

### 程序配置优化
```json
{
  "performance": {
    "enable_optimization": true,
    "use_fast_math": true,
    "low_memory_mode": true
  }
}
```

## 🔒 安全注意事项

1. **高度限制**: 最小投弹高度50米，确保安全
2. **距离验证**: 最大投弹距离50公里，避免误操作
3. **数据校验**: 自动验证输入数据合理性
4. **连接监控**: 实时监控MAVLink连接状态
5. **日志记录**: 完整记录所有操作和计算过程

## 📞 技术支持

- **日志文件**: `/tmp/bomb_release.log`
- **配置文件**: `config_linux.json`
- **测试脚本**: `test_functionality.py`
- **文档**: `README.md`

---

**⚠️ 重要提醒**: 
- 本程序仅用于竞赛和教学目的
- 实际应用需遵守相关法律法规
- 使用前请充分测试和验证
- 确保在安全环境下操作
