import json
from typing import Optional
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("aiohttp 库未安装，请运行 pip install aiohttp 安装依赖")


@register("astrbot_plugin_waterctl", "YourName", "蓝牙水控器控制插件，对接 waterctl 项目", "1.0.0")
class WaterCtlPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.bridge_url: str = "http://localhost:5000"
        # 从配置中读取桥接程序地址
        config = context.get_config()
        if config:
            self.bridge_url = config.get("bridge_url", self.bridge_url).rstrip('/')
        logger.info(f"桥接程序地址: {self.bridge_url}")

    async def initialize(self):
        """插件初始化"""
        if not AIOHTTP_AVAILABLE:
            logger.error("aiohttp 库未安装，插件无法正常工作")
        else:
            logger.info("waterctl 插件已初始化")
            # 检查桥接程序是否可用
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.bridge_url}/health", timeout=aiohttp.ClientTimeout(total=3)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            logger.info(f"桥接程序连接成功: {data}")
                        else:
                            logger.warning(f"桥接程序响应异常: {resp.status}")
            except Exception as e:
                logger.warning(f"无法连接到桥接程序: {e}，请确保桥接程序正在运行")

    async def _api_request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        """发送 HTTP 请求到桥接程序"""
        if not AIOHTTP_AVAILABLE:
            return {"error": "aiohttp 库未安装"}
        
        url = f"{self.bridge_url}{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, 
                    url, 
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    result = await resp.json()
                    return result
        except aiohttp.ClientError as e:
            logger.error(f"HTTP 请求失败: {e}")
            return {"error": f"无法连接到桥接程序: {e}"}
        except Exception as e:
            logger.error(f"请求异常: {e}")
            return {"error": str(e)}

    @filter.command("waterctl")
    async def waterctl_command(self, event: AstrMessageEvent):
        """蓝牙水控器控制命令"""
        if not AIOHTTP_AVAILABLE:
            yield event.plain_result("❌ 错误：aiohttp 库未安装，请运行 `pip install aiohttp` 安装依赖")
            return
        
        args = event.message_str.strip().split()
        if len(args) < 2:
            yield event.plain_result(
                "📖 使用说明：\n"
                "  /waterctl scan - 扫描附近的蓝牙水控器设备\n"
                "  /waterctl connect <设备地址> - 连接到指定设备\n"
                "  /waterctl on - 打开水控器\n"
                "  /waterctl off - 关闭水控器\n"
                "  /waterctl status - 查看设备状态\n\n"
                f"🌐 桥接程序地址: {self.bridge_url}"
            )
            return
        
        subcommand = args[1].lower()
        
        if subcommand == "scan":
            yield event.plain_result("🔍 正在扫描附近的蓝牙设备...")
            result = await self._api_request("GET", "/scan")
            if "error" in result:
                yield event.plain_result(f"❌ 扫描失败: {result['error']}")
            elif "devices" in result:
                devices = result["devices"]
                if not devices:
                    yield event.plain_result("❌ 未发现任何蓝牙设备")
                else:
                    response = "📱 发现的蓝牙设备：\n\n"
                    for i, device in enumerate(devices, 1):
                        response += f"{i}. {device.get('name', '未知设备')}\n"
                        response += f"   地址: {device.get('address', 'N/A')}\n"
                        response += f"   RSSI: {device.get('rssi', 'N/A')} dBm\n\n"
                    yield event.plain_result(response)
            else:
                yield event.plain_result(f"❌ 未知响应: {result}")
        
        elif subcommand == "connect":
            if len(args) < 3:
                yield event.plain_result("❌ 请提供设备地址，例如：/waterctl connect AA:BB:CC:DD:EE:FF")
                return
            
            address = args[2].upper()
            result = await self._api_request("POST", "/connect", {"address": address})
            if "error" in result:
                yield event.plain_result(f"❌ 连接失败: {result['error']}")
            elif result.get("success"):
                yield event.plain_result(f"✅ {result.get('message', '已连接到设备')}")
            else:
                yield event.plain_result(f"❌ 连接失败: {result}")
        
        elif subcommand == "on":
            result = await self._api_request("POST", "/control/on")
            if "error" in result:
                yield event.plain_result(f"❌ 操作失败: {result['error']}")
            elif result.get("success"):
                yield event.plain_result(f"✅ {result.get('message', '水控器已打开')}")
            else:
                yield event.plain_result(f"❌ 操作失败: {result}")
        
        elif subcommand == "off":
            result = await self._api_request("POST", "/control/off")
            if "error" in result:
                yield event.plain_result(f"❌ 操作失败: {result['error']}")
            elif result.get("success"):
                yield event.plain_result(f"✅ {result.get('message', '水控器已关闭')}")
            else:
                yield event.plain_result(f"❌ 操作失败: {result}")
        
        elif subcommand == "status":
            result = await self._api_request("GET", "/status")
            if "error" in result:
            if "error" in result:
                yield event.plain_result(f"❌ 获取状态失败: {result['error']}")
            else:
                address = result.get("device_address", "未设置")
                connected = result.get("connected", False)
                status_icon = "✅" if connected else "❌"
                status_text = "已连接" if connected else "未连接"
                yield event.plain_result(
                    f"{status_icon} 设备状态：{status_text}\n"
                    f"设备地址: {address}\n"
                    f"桥接程序: {self.bridge_url}"
                )
        
        else:
            yield event.plain_result(f"❌ 未知命令: {subcommand}\n使用 /waterctl 查看帮助")
