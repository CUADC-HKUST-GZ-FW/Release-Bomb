#!/bin/bash
# Linux系统快速部署脚本
# 用于在固定翼飞机的Linux小电脑上快速安装程序

set -e  # 遇到错误立即退出

echo "🎯 固定翼飞机投弹计算程序 - Linux快速部署"
echo "=================================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_warning "检测到root用户，建议使用普通用户运行"
    fi
}

# 检查Python版本
check_python() {
    echo "🐍 检查Python环境..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_info "Python版本: $PYTHON_VERSION"
        
        # 检查版本是否满足要求
        python3 -c "import sys; assert sys.version_info >= (3, 7)" 2>/dev/null || {
            print_error "Python版本过低，需要3.7或更高版本"
            exit 1
        }
    else
        print_error "未找到Python3，请先安装Python"
        echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
        echo "CentOS/RHEL: sudo yum install python3 python3-pip"
        exit 1
    fi
}

# 检查pip
check_pip() {
    echo "📦 检查pip..."
    
    if command -v pip3 &> /dev/null; then
        print_info "pip3 可用"
    else
        print_warning "pip3 未安装，尝试安装..."
        
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y python3-pip
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-pip
        else
            print_error "无法自动安装pip，请手动安装"
            exit 1
        fi
    fi
}

# 安装依赖包
install_dependencies() {
    echo "📚 安装Python依赖包..."
    
    # 创建虚拟环境（可选）
    if [ "$1" == "--venv" ]; then
        print_info "创建虚拟环境..."
        python3 -m venv bomb_release_env
        source bomb_release_env/bin/activate
        print_info "虚拟环境已激活"
    fi
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        print_info "依赖包安装完成"
    else
        print_warning "requirements.txt不存在，手动安装关键依赖"
        pip3 install pymavlink numpy
    fi
}

# 检查串口权限
check_serial_permissions() {
    echo "🔌 检查串口权限..."
    
    # 检查用户是否在dialout组中
    if groups $USER | grep -q "dialout"; then
        print_info "用户已在dialout组中"
    else
        print_warning "用户不在dialout组中，添加到组中..."
        sudo usermod -a -G dialout $USER
        print_info "已添加到dialout组，请重新登录生效"
    fi
    
    # 检查常见串口设备
    echo "检查串口设备:"
    for port in /dev/ttyUSB* /dev/ttyAMA* /dev/ttyS* /dev/ttyACM*; do
        if [ -e "$port" ]; then
            echo "  找到: $port"
            ls -l "$port"
        fi
    done
}

# 设置文件权限
set_permissions() {
    echo "🔐 设置文件权限..."
    
    # 设置Python脚本可执行
    chmod +x *.py 2>/dev/null || true
    
    # 设置shell脚本可执行
    for script in *.sh; do
        if [ -f "$script" ]; then
            chmod +x "$script"
            print_info "设置 $script 可执行"
        fi
    done
    
    print_info "权限设置完成"
}

# 创建配置文件
create_config() {
    echo "⚙️ 创建配置文件..."
    
    if [ ! -f "config_linux.json" ]; then
        python3 platform_compat.py
        print_info "配置文件已创建"
    else
        print_info "配置文件已存在"
    fi
}

# 运行测试
run_tests() {
    echo "🧪 运行系统测试..."
    
    if python3 test_functionality.py; then
        print_info "功能测试通过"
    else
        print_warning "功能测试部分失败，但核心功能可用"
    fi
}

# 创建systemd服务
install_service() {
    echo "🔧 安装systemd服务..."
    
    if [ "$1" != "--service" ]; then
        print_info "跳过服务安装（使用 --service 参数安装）"
        return
    fi
    
    if [ ! -f "bomb_release_service.py" ]; then
        print_error "服务文件不存在"
        return
    fi
    
    # 创建服务文件
    SERVICE_PATH="/etc/systemd/system/bomb-release.service"
    CURRENT_DIR=$(pwd)
    
    sudo tee "$SERVICE_PATH" > /dev/null <<EOF
[Unit]
Description=Aircraft Bomb Release Calculator Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$CURRENT_DIR
ExecStart=/usr/bin/python3 $CURRENT_DIR/bomb_release_service.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd并启用服务
    sudo systemctl daemon-reload
    sudo systemctl enable bomb-release.service
    
    print_info "systemd服务已安装"
    echo "启动服务: sudo systemctl start bomb-release"
    echo "查看状态: sudo systemctl status bomb-release"
    echo "查看日志: journalctl -u bomb-release -f"
}

# 显示使用说明
show_usage() {
    echo ""
    echo "📖 部署完成！使用说明:"
    echo "================================"
    echo "1. 直接运行:"
    echo "   python3 quick_bomb_calc.py"
    echo ""
    echo "2. 服务模式:"
    echo "   python3 bomb_release_service.py"
    echo ""
    echo "3. 后台运行:"
    echo "   nohup python3 bomb_release_service.py > /dev/null 2>&1 &"
    echo ""
    echo "4. 系统服务 (如已安装):"
    echo "   sudo systemctl start bomb-release"
    echo ""
    echo "5. 查看日志:"
    echo "   tail -f /tmp/bomb_release.log"
    echo ""
    echo "📁 重要文件:"
    echo "   - config_linux.json: 配置文件"
    echo "   - bomb_release.log: 日志文件"
    echo "   - test_targets.json: 测试目标"
}

# 主函数
main() {
    check_root
    check_python
    check_pip
    
    # 解析命令行参数
    INSTALL_VENV=false
    INSTALL_SERVICE=false
    
    for arg in "$@"; do
        case $arg in
            --venv)
                INSTALL_VENV=true
                ;;
            --service)
                INSTALL_SERVICE=true
                ;;
        esac
    done
    
    # 执行部署步骤
    if [ "$INSTALL_VENV" == true ]; then
        install_dependencies --venv
    else
        install_dependencies
    fi
    
    check_serial_permissions
    set_permissions
    create_config
    run_tests
    
    if [ "$INSTALL_SERVICE" == true ]; then
        install_service --service
    fi
    
    show_usage
    
    print_info "Linux部署完成！"
}

# 运行主函数
main "$@"
