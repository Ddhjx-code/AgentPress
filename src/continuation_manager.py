"""
长篇小说续写管理器
管理长篇小说的多阶段创作、上下文传递和持续性文档累积
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from .documentation_manager import DocumentationManager
from .text_proofreader import TextProofreader


class ContinuationManager:
    """
    管理长篇小说的多阶段续写流程
    """

    def __init__(self, project_name: str, base_path: str = "output/projects"):
        """
        初始化续写管理器

        Args:
            project_name: 项目名称，用于标识整个长篇小说
            base_path: 项目存储的根目录
        """
        self.project_name = project_name
        self.base_path = Path(base_path) / project_name
        self.project_file = self.base_path / f"{project_name}_project.json"

        # 创建项目目录
        self.base_path.mkdir(parents=True, exist_ok=True)

        # 如果项目已存在，加载现有信息
        self.project_info = self._load_project_info()

    def _load_project_info(self) -> Dict[str, Any]:
        """加载已有的项目信息"""
        if self.project_file.exists():
            try:
                with open(self.project_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ 加载项目信息失败: {e}")
                return self._create_default_project_info()
        else:
            return self._create_default_project_info()

    def _create_default_project_info(self) -> Dict[str, Any]:
        """创建默认项目信息"""
        return {
            "project_name": self.project_name,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_chapters": 0,
            "total_words": 0,
            "total_sessions": 0,
            "continuation_points": [],  # 存储各阶段的续写点
            "global_summary": "",      # 整个小说的概要
            "status": "in_progress"    # 新增状态: in_progress, completed
        }

    def save_project_info(self):
        """保存项目信息"""
        self.project_info["last_updated"] = datetime.now().isoformat()
        with open(self.project_file, 'w', encoding='utf-8') as f:
            json.dump(self.project_info, f, ensure_ascii=False, indent=2)

    def start_new_session(self, continuation_point: str = None) -> Dict[str, Any]:
        """
        开始新的续写会话

        Args:
            continuation_point: 可以指定从何处开始续写，如果不指定则从最后一处开始

        Returns:
            会话信息，包括上下文、文档管理器、起始章节数等
        """
        session_id = f"session_{self.project_info['total_sessions'] + 1}_{int(datetime.now().timestamp())}"
        session_dir = self.base_path / session_id
        session_dir.mkdir(exist_ok=True)

        # 更新项目信息
        self.project_info["total_sessions"] += 1
        self.project_info["last_updated"] = datetime.now().isoformat()

        # 计算起始章节号
        start_chapter_num = sum([cp['generated_chapters'] for cp in self.project_info['continuation_points']], 0) + 1

        session_info = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "start_chapter_num": start_chapter_num,  # 起始章节编号
            "previous_content_file": None,           # 如果有续写点，指向前面的内容
            "session_dir": str(session_dir),
            "session_log": session_dir / "session_log.md"
        }

        # 检查是否有之前的续写点
        if self.project_info['continuation_points']:
            if continuation_point:
                # 查找指定的续写点
                for cp in self.project_info['continuation_points']:
                    if cp['session_id'] == continuation_point:
                        session_info["previous_content_file"] = cp['content_file']
                        session_info["start_chapter_num"] = cp['last_chapter'] + 1
                        break
            else:
                # 使用最后一个续写点（这是最常见的情况）
                last_cp = self.project_info['continuation_points'][-1]
                session_info["previous_content_file"] = last_cp['content_file']
                session_info["start_chapter_num"] = last_cp['last_chapter'] + 1

        # 记录会话日志
        with open(session_info["session_log"], 'w', encoding='utf-8') as f:
            f.write(f"# 续写会话：{session_id}\n")
            f.write(f"开始时间：{session_info['start_time']}\n")
            f.write(f"起始章节编号：{session_info['start_chapter_num']}\n")
            if session_info["previous_content_file"]:
                f.write(f"续写起点：{os.path.basename(session_info['previous_content_file'])}\n")
            else:
                f.write("续写起点：新故事开始\n")
            f.write(f"工作目录：{session_dir}\n")

        self.save_project_info()
        return session_info

    def save_session_result(self, session_id: str, generated_content: str,
                           generated_chapters: int, documentation: DocumentationManager = None):
        """
        保存会话结果，创建新的续写点

        Args:
            session_id: 会话ID
            generated_content: 生成的故事内容
            generated_chapters: 这轮生成的章节数
            documentation: 文档管理器
        """
        session_dir = self.base_path / session_id

        # 保存生成的内容
        content_file = session_dir / f"{session_id}_content.md"
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(generated_content)

        # 更新总统计
        last_chapter_num = self.project_info.get('total_chapters', 0)
        self.project_info['total_chapters'] += generated_chapters
        self.project_info['total_words'] += len(generated_content)

        # 创建续写点记录
        continuation_point = {
            "session_id": session_id,
            "content_file": str(content_file),
            "generated_chapters": generated_chapters,
            "generated_words": len(generated_content),
            "last_chapter": last_chapter_num + generated_chapters,
            "session_complete_time": datetime.now().isoformat(),
            "session_dir": str(session_dir)
        }

        # 更新文档管理器，保存为项目级别的文档
        if documentation:
            project_doc_path = session_dir / f"{self.project_name}_story_documentation.json"
            # 由于DocumentationManager需要从字典数据创建文档，我们可以重用这个实例
            # 这里将文档保存到项目级别，以支持持续累积
            documentation.save_path = str(project_doc_path)  # 更新保存路径
            documentation._save_documentation()

        self.project_info['continuation_points'].append(continuation_point)
        self.save_project_info()

        print(f"✅ 会话结果已保存，续写点已更新: {continuation_point['last_chapter']}章")

    def get_continuation_context(self, session_id: str) -> str:
        """
        获取续写上下文（以前章节的内容）

        Args:
            session_id: 当前会话ID

        Returns:
            用于AI参考的上下文字符串
        """
        context_content = ""

        # 避免将完整的上下文作为prompt传递，而是限制字数以控制成本

        if not self.project_info['continuation_points']:
            return ""  # 没有上下文，这是第一次写作

        # 找到当前会话之前的续写点
        previous_parts = []
        for cp in self.project_info['continuation_points']:
            if 'last_session_loaded' not in locals():
                last_session_loaded = cp['session_id']

            if cp['session_id'] < session_id:  # 假设session_id按顺序创建
                # 为了防止上下文过长，我们只保留摘要或最近几章
                content_file = cp['content_file']
                if os.path.exists(content_file):
                    with open(content_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 只保留核心章节（例如最后3章或前2000字符）
                        if len(content) > 3000:  # 如果内容很长，只保留前面部分提供概念参考
                            # 尝试提取概要而不是全文
                            extract_from = min(2000, len(content))
                            partial_content = self._extract_context_from_content(content)
                            previous_parts.append(partial_content)
                        else:
                            previous_parts.append(content)

        context_content = "\n\n== 之前的写作内容（续写参考）==\n\n".join(previous_parts)

        # 使用文本校对器优化上下文，使其更清晰
        if context_content:
            proofreader = TextProofreader()
            context_content = proofreader.proofread_text(context_content)

        return context_content

    def _extract_context_from_content(self, content: str) -> str:
        """
        从完整内容中提取关键续写上下文
        改进版：不仅提取章节，还提取关键角色、世界观、重要情节等信息

        Args:
            content: 完整的内容

        Returns:
            提取的关键上下文
        """
        import re

        # 尝試提取各种形式的章节标题
        chapter_title_patterns = [
            r'^\s*第[\d\w\u4e00-\u9fff]+章',       # 第X章
            r'^\s*第[\d\w\u4e00-\u9fff]+回',       # 第X回
            r'^\s*第[\d\w\u4e00-\u9fff]+节',       # 第X节
            r'^\s*#.*第[\d\w\u4e00-\u9fff]+章',    # # 第X章
            r'^\s*[一二三四五六七八九十\d]+[、]\s*.*$'  # 一、章节标题 格式
        ]

        # 檢查是否包含这些模式
        has_chapter = any(re.search(pattern, line, re.MULTILINE) for pattern in chapter_title_patterns for line in content.split('\n'))

        if has_chapter:
            # 如果有章节信息，使用章节提取方式
            lines = content.split('\n')
            extracted_context = ""
            current_chapter = ""
            chapter_found_count = 0
            max_chapters = 3  # 最多提取3个章节

            for line in lines:
                line = line.strip()

                # 檢查所有章节标题模式
                is_chapter_title = any(re.match(pattern, line) for pattern in chapter_title_patterns)

                if is_chapter_title:
                    if current_chapter and chapter_found_count < max_chapters:
                        # 添加当前章节到提取内容
                        extracted_context += current_chapter + "\n"
                        chapter_found_count += 1
                        if chapter_found_count >= max_chapters:
                            # 添加最后章节的开头部分
                            current_chapter = line + "\n"
                            # 限制最后章节的长度
                            words_added = 0
                            break
                    current_chapter = line + "\n"
                elif current_chapter and line and len(line) > 5:  # 添加内容到当前章节
                    current_chapter += line + "\n"
                    # 控制单个章节内容的量，避免单个章节太长
                    if len(current_chapter) > 1000 and chapter_found_count >= max_chapters - 1:
                        current_chapter += "...\n(中间内容省略)\n"
                        break

            # 添加最后一个章节
            if current_chapter and chapter_found_count <= max_chapters:
                extracted_context += current_chapter

            if len(extracted_context) > 2500:
                # 限制为开头和结尾部分
                return extracted_context[:1200] + "\n\n...[中间内容省略以节省上下文]...\n\n" + extracted_context[-1200:]

            return extracted_context
        else:
            # 如果没有章节划分，使用其他方式提取上下文
            # 提取开头和结尾部分（开头通常是背景设定，结尾是最新进展）
            content_len = len(content)
            start_len = min(1000, content_len // 2)
            end_len = min(1000, content_len // 2)

            if content_len <= 2500:
                return content
            else:
                start_part = content[:start_len]
                end_part = content[-end_len:] if end_len > 0 else ""

                extracted = f"【故事开头部分】\n{start_part}\n\n...[中间内容省略]...\n\n【最近的部分】\n{end_part}"
                return extracted

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取特定会话的信息"""
        for cp in self.project_info['continuation_points']:
            if cp['session_id'] == session_id:
                return cp
        return None

    def get_project_summary(self) -> str:
        """获取项目摘要信息"""
        summary = f"""
# 项目: {self.project_info['project_name']}
- 總章数: {self.project_info.get('total_chapters', 0)} 章
- 總字數: {self.project_info.get('total_words', 0)} 字
- 已进行会话数: {self.project_info.get('total_sessions', 0)} 次
- 状态: {self.project_info.get('status', 'in_progress')}
- 创建时间: {self.project_info['created_at']}
- 最后更新: {self.project_info['last_updated']}

## 会话历史:
"""
        for i, cp in enumerate(self.project_info['continuation_points'], 1):
            summary += f"- {i}. 会话 {cp['session_id']}: {cp['generated_chapters']} 章 ({cp['generated_words']} 字) - 到第 {cp['last_chapter']} 章\n"

        return summary

    def load_documentation_for_session(self, session_dir: str) -> DocumentationManager:
        """
        为当前会话加载积累的文档管理器

        Args:
            session_dir: 当前会话目录

        Returns:
            文档管理器实例
        """
        # 查找项目级别的文档文件
        doc_file = Path(session_dir) / f"{self.project_name}_story_documentation.json"

        if doc_file.exists():
            # 如果存在项目档，加载它来继续累积
            print(f"📚 加载累积的文档管理器: {doc_file}")
            return DocumentationManager(save_path=str(doc_file))
        else:
            # 檢查是否有之前的项目文档
            for cp in reversed(self.project_info['continuation_points']):
                prev_doc_path = Path(cp['session_dir']) / f"{self.project_name}_story_documentation.json"
                if prev_doc_path.exists():
                    print(f"📚 从上一个会话加载文档: {prev_doc_path}")
                    # 复制档到当前会话目录
                    import shutil
                    shutil.copy(prev_doc_path, doc_file)
                    return DocumentationManager(save_path=str(doc_file))

        # 创建新的文档管理器
        print("📚 创建新的文档管理器")
        return DocumentationManager(
            story_title=self.project_name,
            save_path=str(doc_file)
        )


def create_continuation_cli_command():
    """
    创建续写命令行界面的示例函数
    这将帮助用户管理和续写他们的长篇小说
    """
    import argparse

    parser = argparse.ArgumentParser(description="长篇小说续写管理器")
    parser.add_argument("project_name", help="项目名称")
    parser.add_argument("--list", action="store_true", help="列出项目信息")
    parser.add_argument("--resume", action="store_true", help="开始新的续写会话")
    parser.add_argument("--summary", action="store_true", help="显示项目摘要")

    args = parser.parse_args()

    manager = ContinuationManager(args.project_name)

    if args.list or args.summary:
        print(manager.get_project_summary())
    elif args.resume:
        # 创建新的续写会话
        session_info = manager.start_new_session()
        print(f"✅ 开始新的续写会话: {session_info['session_id']}")
        print(f"📝 从第 {session_info['start_chapter_num']} 章开始续写")
        print(f"📁 会话目录: {session_info['session_dir']}")
        print(f"💾 项目信息: {session_info['session_log']}")


if __name__ == "__main__":
    # 简单的测试
    import sys
    if len(sys.argv) > 1:
        create_continuation_cli_command()
    else:
        print("续写管理器模块 - 用于长篇小说多阶段撰写")
        print("使用方法: python continuation_manager.py --help")