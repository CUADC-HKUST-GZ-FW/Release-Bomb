from pymavlink import mavutil
import time
import sys

def set_servo_pwm(vehicle, channel, pwm_value):
    """设置舵机指定通道的PWM值"""
    vehicle.mav.command_long_send(
        vehicle.target_system,
        vehicle.target_component,
        mavutil.mavlink.MAV_CMD_DO_SET_SERVO,
        0,                      # 无需确认
        channel,                # 舵机通道
        pwm_value,              # PWM值
        0, 0, 0, 0, 0           # 未使用参数
    )
    print(f"已发送指令：舵机通道 {channel}，PWM值 {pwm_value}")

def main():
    # 配置参数
    serial_port = '/dev/ttyACM0'
    baud_rate = 57600
    servo_channel = 9  # 默认舵机通道

    # 检查命令行参数
    if len(sys.argv) != 2:
        print("用法: python3 servo_control.py [pwm_value]")
        print("其中 pwm_value 必须是1300-1900之间的整数")
        print("示例:")
        print("  设置PWM=1300: python3 servo_control.py 1300")
        print("  设置PWM=1600: python3 servo_control.py 1600")
        print("  设置PWM=1900: python3 servo_control.py 1900")
        return

    try:
        # 解析并验证PWM值
        pwm_value = int(sys.argv[1])
        if not (1300 <= pwm_value <= 1900):
            raise ValueError("PWM值必须在1300到1900之间")

        # 建立串口连接
        vehicle = mavutil.mavlink_connection(serial_port, baud=baud_rate)
        
        # 等待飞控心跳
        print("等待飞控连接...")
        vehicle.wait_heartbeat(timeout=10)
        print("飞控连接成功")
        
        # 发送PWM指令
        set_servo_pwm(vehicle, servo_channel, pwm_value)
        
        # 等待指令生效
        time.sleep(0.5)

    except ValueError as ve:
        print(f"参数错误：{str(ve)}")
    except Exception as e:
        print(f"出错：{str(e)}")
    finally:
        # 关闭连接
        if 'vehicle' in locals() and hasattr(vehicle, 'close'):
            vehicle.close()
        print("程序结束")

if __name__ == "__main__":
    main()
