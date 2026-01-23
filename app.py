"""
AgentPress 主应用程序入口
此文件负责启动Web UI服务器
"""
import uvicorn
from apps.web_ui import app


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    启动AgentPress Web服务器
    """
    print("\n" + "="*60)
    print("🚀 AgentPress 增强版已启动")
    print(f"🌐 访问地址: http://{host}:{port}")
    print(f"🔄 热重载: {'开启' if reload else '关闭'}")
    print("="*60)

    uvicorn.run(
        "apps.web_ui:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='AgentPress 增强版')
    parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址')
    parser.add_argument('-p', '--port', type=int, default=8000, help='服务器端口')
    parser.add_argument('--reload', action='store_true', help='启用热重载模式')

    args = parser.parse_args()

    start_server(args.host, args.port, args.reload)