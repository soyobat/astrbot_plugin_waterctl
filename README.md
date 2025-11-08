# astrbot_plugin_waterctl

蓝牙水控器控制插件，对接 [waterctl](https://github.com/celesWuff/waterctl) 项目。

## 架构说明

由于 AstrBot 通常部署在云服务器上，而蓝牙设备需要在物理距离内才能连接，因此采用**桥接架构**：

```
┌─────────────────┐         HTTP API          ┌──────────────┐         Bluetooth         ┌──────────┐
│  云服务器        │  ───────────────────────>  │  本地设备     │  ───────────────────>  │  热水器   │
│  AstrBot 插件    │                            │  桥接程序     │                         │          │
└─────────────────┘                            └──────────────┘                         └──────────┘
```

- **AstrBot 插件**：运行在云服务器上，通过 HTTP 调用桥接程序
- **桥接程序**：运行在宿舍本地设备上（如树莓派、电脑等），通过蓝牙控制热水器

## 功能

- 通过 AstrBot 控制蓝牙水控器
- 支持开关控制
- 支持温度调节
- 支持设备扫描和连接

## 安装步骤

### 1. 安装 AstrBot 插件（云服务器）

1. 将插件放置到 AstrBot 的插件目录
2. 安装依赖：`pip install -r requirements.txt`
3. 在 AstrBot 中启用插件
4. 配置桥接程序地址（见下方配置说明）

### 2. 安装桥接程序（本地设备）

在宿舍本地设备上（需要支持蓝牙，如树莓派、电脑等）：

1. 下载 `bridge.py` 文件
2. 安装依赖：`pip install -r bridge_requirements.txt`
3. 运行桥接程序：`python bridge.py`
4. 桥接程序默认监听 `http://0.0.0.0:5000`

**注意**：如果本地设备在局域网内，需要确保云服务器能够访问到本地设备的 IP 地址。可以使用：
- 内网穿透工具（如 frp、ngrok）
- VPN 连接
- 公网 IP + 端口转发

## 使用

- `/waterctl scan` - 扫描附近的蓝牙水控器设备
- `/waterctl connect <设备地址>` - 连接到指定设备
- `/waterctl on` - 打开水控器
- `/waterctl off` - 关闭水控器
- `/waterctl temp <温度>` - 设置温度（0-100）
- `/waterctl status` - 查看设备状态

## 配置

### AstrBot 插件配置

在插件配置中可以设置以下参数：

- `bridge_url`: 桥接程序地址（默认：`http://localhost:5000`）
  - 如果桥接程序在同一台机器：`http://localhost:5000`
  - 如果在局域网内：`http://192.168.1.100:5000`
  - 如果通过内网穿透：`http://your-domain.com:port`

### 桥接程序配置

桥接程序可以通过环境变量配置：

- `PORT`: 监听端口（默认：5000）

示例：
```bash
PORT=8080 python bridge.py
```

## 重要提示

⚠️ **命令格式调整**：当前实现中的命令格式（开关、温度设置）是示例性的，可能需要根据实际设备协议进行调整。

要获取正确的命令格式，可以：

1. 查看 [waterctl 项目源代码](https://github.com/celesWuff/waterctl) 中的实现
2. 使用蓝牙调试工具（如 nRF Connect）监控 waterctl Web 应用发送的实际数据
3. 根据设备文档或逆向工程确定协议格式

修改命令格式：编辑 `bridge.py` 文件中 `turn_on()`、`turn_off()` 和 `set_temperature()` 函数中的 `command = bytes([...])` 部分。

## 系统要求

### AstrBot 插件（云服务器）
- Python 3.7+
- aiohttp 库

### 桥接程序（本地设备）
- Python 3.7+
- 支持蓝牙的计算机（Windows/Linux/macOS/树莓派）
- bleak 库
- flask 和 flask-cors 库

## 安全建议

1. **内网访问**：如果桥接程序暴露在公网，建议：
   - 使用 HTTPS（可以通过 nginx 反向代理）
   - 添加身份验证（API Key 或 Token）
   - 使用防火墙限制访问 IP

2. **本地安全**：确保桥接程序只监听必要的接口，避免暴露敏感信息

## 测试桥接程序

### 方法 1: 使用测试脚本（推荐）

1. **安装测试依赖**：
   ```bash
   pip install -r test_requirements.txt
   ```

2. **启动桥接程序**（在另一个终端）：
   ```bash
   python bridge.py
   ```

3. **运行测试脚本**：
   ```bash
   # 基础测试（不包含连接）
   python test_bridge.py
   
   # 完整测试（包含连接和控制）
   python test_bridge.py connect AA:BB:CC:DD:EE:FF
   ```

   测试脚本会依次测试：
   - ✅ 健康检查
   - ✅ 设备扫描
   - ✅ 设备连接（如果提供了地址）
   - ✅ 状态查询
   - ✅ 打开/关闭控制
   - ✅ 温度设置

### 方法 2: 使用 curl 命令

```bash
# 健康检查
curl http://localhost:5000/health

# 扫描设备
curl http://localhost:5000/scan

# 连接设备
curl -X POST http://localhost:5000/connect \
  -H "Content-Type: application/json" \
  -d '{"address": "AA:BB:CC:DD:EE:FF"}'

# 获取状态
curl http://localhost:5000/status

# 打开水控器
curl -X POST http://localhost:5000/control/on

# 设置温度
curl -X POST http://localhost:5000/control/temp \
  -H "Content-Type: application/json" \
  -d '{"temperature": 40}'

# 关闭水控器
curl -X POST http://localhost:5000/control/off
```

### 方法 3: 使用浏览器

直接在浏览器中访问：
- `http://localhost:5000/health` - 健康检查
- `http://localhost:5000/status` - 获取状态
- `http://localhost:5000/scan` - 扫描设备（需要等待）

## 故障排查

1. **无法连接到桥接程序**
   - 检查桥接程序是否正在运行
   - 检查网络连接和防火墙设置
   - 验证 `bridge_url` 配置是否正确

2. **蓝牙设备无法连接**
   - 确保本地设备支持蓝牙
   - 检查设备是否在蓝牙范围内
   - 查看桥接程序的日志输出

3. **命令执行失败**
   - 检查命令格式是否正确（可能需要根据实际设备调整）
   - 查看桥接程序的错误日志

## 支持

[帮助文档](https://astrbot.app)  
[waterctl 项目](https://github.com/celesWuff/waterctl)
