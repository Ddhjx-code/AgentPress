#!/usr/bin/env python3
"""
AgentPress 命令行界面
提供参数化配置和交互式控制功能
"""
import argparse
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any
from typing import TYPE_CHECKING
import json

# 添加项目路径（将当前目录添加到Python路径的前面）
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

if TYPE_CHECKING:
    # 仅用于静态类型检查，避免IDE警告
    from config import HierarchicalConfigManager
    from config import DEFAULT_SETTINGS

# 导入项目模块（使用适当的路径调整）
try:
    import sys
    from pathlib import Path
    project_path = Path(__file__).parent

    # 确保当前路径在modules路径中
    if str(project_path) not in sys.path:
        sys.path.insert(0, str(project_path))

    # 实际运行时的处理逻辑
    try:
        config_settings_path = project_path / "config" / "settings.py"
        import importlib.util
        spec = importlib.util.spec_from_file_location("settings", config_settings_path)
        settings_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings_module)
        HierarchicalConfigManager = settings_module.HierarchicalConfigManager
    except (FileNotFoundError, ModuleNotFoundError):
        # 如果文件不存在（如在打包环境），使用标准导入
        try:
            import config
            # 直接从模块对象获取
            HierarchicalConfigManager = getattr(config.settings, 'HierarchicalConfigManager', None)
            if HierarchicalConfigManager is None:
                import importlib
                config_settings_module = importlib.import_module('config.settings')
                HierarchicalConfigManager = getattr(config_settings_module, 'HierarchicalConfigManager', None)
        except ImportError:
            import importlib
            config_settings_module = importlib.import_module('config.settings')
            HierarchicalConfigManager = config_settings_module.HierarchicalConfigManager

    # 现在导入其他模块
    from core.agent_manager import AgentManager
    from core.conversation_manager import ConversationManager
    from core.workflow_controller import WorkflowController
    from src.documentation_manager import DocumentationManager
    from phases import NovelWorkflowOrchestrator
    from utils import load_all_prompts
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    from autogen_core.models import ModelInfo, ModelFamily
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("当前搜索路径:", sys.path)
    raise


def create_argument_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="AgentPress - AI驱动的小说生成系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python cli.py generate "我的故事概念"
  python cli.py generate "我的故事概念" --total-target-length 8000
  python cli.py info
  python cli.py config --show-current
  python cli.py generate "故事概念" --enable-manual-control --config-file my_config.json
        """
    )

    # 主命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # generate 子命令
    generate_parser = subparsers.add_parser('generate', help='生成小说')
    generate_parser.add_argument('concept', nargs='?', help='故事概念/主题')
    generate_parser.add_argument('--total-target-length', type=int, help='目标总字数')
    generate_parser.add_argument('--min-chinese-chars', type=int, help='最小汉字数')
    generate_parser.add_argument('--target-length-per-chapter', type=int, help='每章目标字数')
    generate_parser.add_argument('--chapter-target-chars', type=int, help='每章目标汉字数')
    generate_parser.add_argument('--enable-dynamic-chapters', action='store_true', help='启用动态多章节生成')
    generate_parser.add_argument('--enable-manual-control', action='store_true', help='启用人工控制模式')
    generate_parser.add_argument('--model-api-key', help='模型API密钥')
    generate_parser.add_argument('--model-base-url', help='模型API基础URL')
    generate_parser.add_argument('--config-file', help='配置文件路径')
    generate_parser.add_argument('--prompts-dir', default='prompts', help='提示词目录路径')

    # info 子命令
    info_parser = subparsers.add_parser('info', help='显示系统信息')
    info_parser.add_argument('--verbose', action='store_true', help='显示详细信息')

    # config 子命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_parser.add_argument('--show-current', action='store_true', help='显示当前配置')
    config_parser.add_argument('--show-default', action='store_true', help='显示默认配置')
    config_parser.add_argument('--export', help='导出当前配置到JSON文件')
    config_parser.add_argument('--list-parameters', action='store_true', help='列出所有可配置参数')
    config_parser.add_argument('--config-file', help='配置文件路径')

    # status 子命令
    status_parser = subparsers.add_parser('status', help='显示工作流状态')

    return parser


def load_story_concept(concept_arg: str) -> str:
    """加载故事概念，优先使用直接参数，备选test_concept.txt文件"""
    if concept_arg:
        return concept_arg

    # 在当前目录查找test_concept.txt
    test_concept_path = Path("test_concept.txt")
    if test_concept_path.exists():
        with open(test_concept_path, 'r', encoding='utf-8') as f:
            return f.read().strip()

    # 如果没有文件也没有参数，则提示用户
    raise ValueError("必须提供故事概念: 作为参数或者在 test_concept.txt 文件中")


def run_generate_command(args: argparse.Namespace):
    """执行generate命令"""
    print("🚀 启动 AgentPress 小说生成系统...")

    # 初始化配置管理器
    config_manager = HierarchicalConfigManager(
        config_file=args.config_file or "config.json"
    )

    # 从参数加载配置（最高优先级）
    cli_config = {}
    if args.total_target_length is not None:
        cli_config['total_target_length'] = args.total_target_length
    if args.min_chinese_chars is not None:
        cli_config['min_chinese_chars'] = args.min_chinese_chars
    if args.target_length_per_chapter is not None:
        cli_config['target_length_per_chapter'] = args.target_length_per_chapter
    if args.chapter_target_chars is not None:
        cli_config['chapter_target_chars'] = args.chapter_target_chars
    if args.enable_dynamic_chapters:
        cli_config['enable_dynamic_chapters'] = True
    else:
        # 只有显式设置了 --enable-dynamic-chapters 才设为 True, 否则保持默认值
        pass

    if cli_config:
        config_manager.load_from_cli_args(cli_config)

    # 打印当前使用的配置
    creation_config = config_manager.get_creation_config()
    print(f"\n📋 当前配置:")
    print(f"   目标总字数: {creation_config['total_target_length']}")
    print(f"   最小汉字数: {creation_config['min_chinese_chars']}")
    print(f"   每章目标字数: {creation_config['target_length_per_chapter']}")
    print(f"   启用动态章节: {creation_config['enable_dynamic_chapters']}")

    async def run_workflow():
        # 加载提示词
        prompts_dir = Path(args.prompts_dir)
        prompts = load_all_prompts(prompts_dir)

        if not prompts:
            print("❌ 无法加载提示词文件")
            return

        print("✅ 成功加载提示词")

        # 获取并验证密钥
        api_key = args.model_api_key or config_manager.get_api_key()
        if not api_key:
            api_key = os.getenv("QWEN_API_KEY")

        if not api_key:
            print("❌ 未找到API密钥，请通过以下方式之一设置:")
            print("   1. 命令行参数 --model-api-key")
            print("   2. 环境变量 QWEN_API_KEY")
            print("   3. 配置文件")
            return

        # 创建模型客户端
        model_client = OpenAIChatCompletionClient(
            model="qwen3-max",
            api_key=api_key,
            base_url=args.model_base_url or config_manager.get_model_config()['base_url'],
            model_info=ModelInfo(
                vision=False,
                function_calling=True,
                json_output=True,
                structured_output=False,
                family=ModelFamily.GPT_5
            )
        )

        # 创建代理管理器
        agent_manager = AgentManager(model_client)
        initialized = await agent_manager.initialize(prompts)

        if not initialized:
            print("❌ 代理管理器初始化失败")
            return

        print("✅ 代理管理器初始化成功")

        # 创建文档管理器
        documentation_manager = DocumentationManager()

        # 创建工作流协调器
        orchestrator = NovelWorkflowOrchestrator()

        # 加载故事概念
        try:
            concept = load_story_concept(args.concept)
            print(f"📝 使用故事概念: {concept[:100]}{'...' if len(concept) > 100 else ''}")
        except ValueError as e:
            print(f"❌ {e}")
            return

        # 运行完整工作流
        print("\n🔄 开始故事生成流程...")
        result = await orchestrator.run_async_workflow(
            initial_idea=concept,
            multi_chapter=True,
            agent_handlers_map=agent_manager.create_agent_handlers_map(documentation_manager) if agent_manager else None,
            enable_manual_control=args.enable_manual_control
        )

        if result:
            # 保存结果
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)

            # 保存最终故事
            story_file = output_dir / f"generated_story_{len(result['final_story'])}.txt"
            with open(story_file, 'w', encoding='utf-8') as f:
                f.write(result['final_story'])

            print(f"\n✅ 小说生成完成！")
            print(f"📝 字数: {len(result['final_story'])}")
            print(f"💾 保存路径: {story_file}")

            # 显示会议纪要（如果存在）
            conversation_manager = orchestrator.get_conversation_manager()
            if hasattr(conversation_manager, 'get_meeting_minutes_summary'):
                meeting_minutes = conversation_manager.get_meeting_minutes_summary()
                if meeting_minutes:
                    print(f"\n📋 代理讨论摘要:")
                    for meeting in meeting_minutes:
                        print(f"   • {meeting['stage']}: {meeting['summary'][:80]}...")

            # 打印工作流状态
            status_report = orchestrator.get_workflow_status()
            print(f"\n📊 生成统计:")
            print(f"   生成轮次: {status_report.get('total_conversations', 0)}")
            print(f"   版本数量: {status_report.get('total_versions', 0)}")
            print(f"   反馈次数: {status_report.get('total_feedback_rounds', 0)}")
            print(f"   讨论纪要: {status_report.get('total_meeting_minutes', 0)}")

    # 运行异步操作
    try:
        asyncio.run(run_workflow())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 生成过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


def run_info_command(args: argparse.Namespace):
    """执行info命令"""
    # 为静态分析提供类型提示
    try:
        from config.settings import DEFAULT_SETTINGS  # type: ignore
    except ImportError:
        DEFAULT_SETTINGS = None  # 仅为静态分析提供类型提示

    try:
        import importlib.util
        settings_path = Path(__file__).parent / "config" / "settings.py"
        if settings_path.exists():
            spec = importlib.util.spec_from_file_location("config_settings", settings_path)
            settings_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(settings_module)
            DEFAULT_SETTINGS = settings_module.DEFAULT_SETTINGS
        else:
            # 如果打包环境，使用模块导入方式
            try:
                import config
                DEFAULT_SETTINGS = config.settings.DEFAULT_SETTINGS
            except ImportError:
                # 使用importlib方式作为最后备选
                import importlib
                settings_module = importlib.import_module('config.settings')
                DEFAULT_SETTINGS = settings_module.DEFAULT_SETTINGS
    except (ImportError, AttributeError, FileNotFoundError):
        # 如果都无法导入，用通用消息
        print("📚 AgentPress 系统信息")
        print("=" * 50)
        print("配置模块导入失败")
        print(f"版本: 1.0.0")
        print(f"当前工作目录: {os.getcwd()}")
        return

    print("📚 AgentPress 系统信息")
    print("=" * 50)

    # 显示基本系统信息
    print(f"版本: 1.0.0")
    print(f"当前工作目录: {os.getcwd()}")

    if args.verbose:
        # 详细配置显示
        print(f"\n📋 默认配置信息:")
        for config_key, config_val in DEFAULT_SETTINGS.items():
            print(f"  {config_key}: {type(config_val).__name__} ({len(config_val) if isinstance(config_val, (dict, list)) else 'value'})")


def run_config_command(args: argparse.Namespace):
    """执行config命令"""
    config_manager = HierarchicalConfigManager(
        config_file=args.config_file or "config.json"
    )

    if args.show_current:
        ui_config = config_manager.get_ui_config()

        print("📋 当前配置参数:")
        for section, data in ui_config.items():
            if section != "title" and "parameters" in data:
                print(f"\n【{data.get('title', section)}】")
                print(f"  {data.get('description', '')}")
                for param in data["parameters"]:
                    current = param.get("current_value", param.get("default"))
                    print(f"  - {param['name']}: {current} ({param['display_name']})")

    elif args.show_default:
        # 为静态分析提供类型提示
        try:
            from config.settings import DEFAULT_SETTINGS  # type: ignore
        except ImportError:
            DEFAULT_SETTINGS = None  # 仅为静态分析提供类型提示

        try:
            import importlib.util
            settings_path = Path(__file__).parent / "config" / "settings.py"
            if settings_path.exists():
                spec = importlib.util.spec_from_file_location("config_settings", settings_path)
                settings_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(settings_module)
                DEFAULT_SETTINGS = settings_module.DEFAULT_SETTINGS
            else:
                # 如果打包环境，使用模块导入方式
                try:
                    import config
                    DEFAULT_SETTINGS = config.settings.DEFAULT_SETTINGS
                except ImportError:
                    # 使用importlib方式作为最后备选
                    import importlib
                    settings_module = importlib.import_module('config.settings')
                    DEFAULT_SETTINGS = settings_module.DEFAULT_SETTINGS
        except (ImportError, AttributeError, FileNotFoundError):
            print("❌ 无法加载默认配置参数")
            return
        print("📋 默认配置参数:")
        for config_key, config_dict in DEFAULT_SETTINGS.items():
            print(f"\n【{config_key}】")
            for key, value in config_dict.items():
                print(f"  - {key}: {value} ({type(value).__name__})")

    elif args.list_parameters:
        print("📋 可配置参数列表:")
        print("\n命令行参数可以直接使用的配置:")
        print("  --total-target-length: 目标总字数")
        print("  --min-chinese-chars: 最小汉字数")
        print("  --target-length-per-chapter: 每章目标字数")
        print("  --chapter-target-chars: 每章目标汉字数")
        print("  --enable-dynamic-chapters: 启用动态多章节")
        print("  --enable-manual-control: 启用人工控制")
        print("\n环境变量:")
        print("  CREATION_TOTAL_TARGET_LENGTH: 目标总字数")
        print("  CREATION_MIN_CHINESE_CHARS: 最小汉字数")
        print("  MODEL_API_KEY: 模型API密钥")
        print("  MODEL_BASE_URL: 模型API基础URL")

    elif args.export:
        config_manager.write_to_file(args.export)
        print(f"💾 配置已导出到: {args.export}")

    else:
        # 默认显示当前配置
        ui_config = config_manager.get_ui_config()

        print("📋 当前配置参数:")
        for section, data in ui_config.items():
            if section != "title" and "parameters" in data:
                print(f"\n【{data.get('title', section)}】")
                for param in data["parameters"]:
                    current = param.get("current_value", param.get("default"))
                    print(f"  - {param['display_name']}: {current} ({param['name']})")


def run_status_command(args: argparse.Namespace):
    """执行status命令（此命令在运行时才有意义，这里只显示说明）"""
    print("📋 工作流状态命令")
    print("注意: 此命令仅在工作流运行时有意义。")
    print("在工作流运行过程中，您可以使用控制台查看实时状态。")


def main():
    parser = create_argument_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 根据命令执行相应操作
    if args.command == 'generate':
        run_generate_command(args)
    elif args.command == 'info':
        run_info_command(args)
    elif args.command == 'config':
        run_config_command(args)
    elif args.command == 'status':
        run_status_command(args)
    else:
        print(f"❌ 未知命令: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()