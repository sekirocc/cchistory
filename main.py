#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code History Exporter
Export JSONL files from ~/.claude/projects to readable text files
"""

import os
import json
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Union, List, Tuple


# Type aliases
ContentData = Union[str, List[Dict[str, Any]]]
ContentAnalysis = Dict[str, Union[str, bool]]


# Language configuration
LANGUAGES = {
    'zh': {'user': '👤 用户', 'assistant': '🤖 助手', 'tool': '🔧', 'result': '✅ 结果:', 'param': '参数:'},
    'en': {'user': '👤 User', 'assistant': '🤖 Assistant', 'tool': '🔧', 'result': '✅ Result:', 'param': 'Args:'},
    'es': {'user': '👤 Usuario', 'assistant': '🤖 Asistente', 'tool': '🔧', 'result': '✅ Resultado:', 'param': 'Parámetros:'},
    'fr': {'user': '👤 Utilisateur', 'assistant': '🤖 Assistant', 'tool': '🔧', 'result': '✅ Résultat:', 'param': 'Paramètres:'},
    'de': {'user': '👤 Benutzer', 'assistant': '🤖 Assistent', 'tool': '🔧', 'result': '✅ Ergebnis:', 'param': 'Parameter:'},
    'ja': {'user': '👤 ユーザー', 'assistant': '🤖 アシスタント', 'tool': '🔧', 'result': '✅ 結果:', 'param': '引数:'},
    'ko': {'user': '👤 사용자', 'assistant': '🤖 어시스턴트', 'tool': '🔧', 'result': '✅ 결과:', 'param': '매개변수:'},
    'ru': {'user': '👤 Пользователь', 'assistant': '🤖 Ассистент', 'tool': '🔧', 'result': '✅ Результат:', 'param': 'Параметры:'},
    'pt': {'user': '👤 Usuário', 'assistant': '🤖 Assistente', 'tool': '🔧', 'result': '✅ Resultado:', 'param': 'Parâmetros:'},
    'it': {'user': '👤 Utente', 'assistant': '🤖 Assistente', 'tool': '🔧', 'result': '✅ Risultato:', 'param': 'Parametri:'},
}


class ClaudeHistoryExporter:
    """Claude history record exporter"""

    # Class constants
    SEPARATOR_LENGTH = 80
    MAX_RESULT_LENGTH = 5000
    MAX_FILENAME_BYTES = 60

    def __init__(self, projects_dir: Optional[str] = None, output_dir: str = "output", lang: str = 'zh'):
        """
        Initialize the exporter

        Args:
            projects_dir: Path to Claude projects directory, default is $HOME/.claude/projects
            output_dir: Output directory path, default is ./output
            lang: Language code, default is Chinese (zh)
        """
        self.projects_dir = projects_dir or os.path.expanduser("~/.claude/projects")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.lang = lang if lang in LANGUAGES else 'zh'
        self.texts = LANGUAGES[self.lang]

    def export_all(self):
        """Export all project history records"""
        if not os.path.exists(self.projects_dir):
            print(f"Error: Projects directory does not exist: {self.projects_dir}")
            return

        # Iterate through all project directories
        for project_name in sorted(os.listdir(self.projects_dir)):
            project_path = os.path.join(self.projects_dir, project_name)

            if not os.path.isdir(project_path):
                continue

            # Skip hidden directories
            if project_name.startswith('.'):
                continue

            print(f"\nProcessing project: {project_name}")
            self.export_project(project_name, project_path)

        print("\n✓ Export completed!")

    def export_project(self, project_name: str, project_path: str):
        """
        Export a single project's history records

        Args:
            project_name: Project name (encoded path)
            project_path: Full path to the project
        """
        # Decode project name to readable path
        readable_name = self.decode_project_name(project_name)
        print(f"  Readable name: {readable_name}")

        # Create project output directory
        safe_name = readable_name.replace('/', '-').strip('-')
        project_output_dir = self.output_dir / safe_name
        project_output_dir.mkdir(parents=True, exist_ok=True)

        # Process all jsonl files in the project
        jsonl_files = [f for f in os.listdir(project_path)
                      if f.endswith('.jsonl') and os.path.isfile(os.path.join(project_path, f))]

        for jsonl_file in sorted(jsonl_files):
            print(f"  Processing file: {jsonl_file}")
            jsonl_path = os.path.join(project_path, jsonl_file)
            self.process_jsonl_file(jsonl_path, project_output_dir, jsonl_file)

    def process_jsonl_file(self, jsonl_path: str, output_dir: Path, jsonl_name: str) -> None:
        """
        Process single JSONL file

        Args:
            jsonl_path: Path to JSONL file
            output_dir: Output directory
            jsonl_name: JSONL file name
        """
        conversation_content = ""
        message_count = 0

        # Used to merge consecutive messages from the same role
        pending_messages = []  # List of accumulated messages

        # Read and parse JSONL file
        try:
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError as e:
                        print(f"    Warning: Failed to parse JSON at line {line_num}: {e}")
                        continue

                    # Skip snapshot messages
                    if data.get('type') == 'file-history-snapshot':
                        continue

                    # Only process user and assistant type messages
                    msg_type = data.get('type', '')
                    if msg_type not in ['user', 'assistant']:
                        continue

                    message = data.get('message', {})
                    role = message.get('role', '')
                    content = message.get('content', '')

                    # Skip if content is None
                    if content is None:
                        continue

                    # Analyze content to extract text and tool information
                    content_info = self._analyze_content(content)
                    text_content = content_info['text']
                    has_tools = content_info['has_tools']

                    # Skip if empty content and no tools
                    if not text_content.strip() and not has_tools:
                        continue

                    # Create message object
                    msg_obj = {
                        'data': data,
                        'role': role,
                        'text': text_content,
                        'has_tools': has_tools
                    }

                    # Determine if previous accumulated messages should be output
                    should_flush = False

                    if not pending_messages:
                        # First message
                        pending_messages.append(msg_obj)
                    elif role != pending_messages[0]['role']:
                        # Role changed, output previous accumulated messages
                        should_flush = True
                    else:
                        # Same role, accumulate messages (regardless of tools)
                        pending_messages.append(msg_obj)

                    if should_flush:
                        # Output previous accumulated messages
                        formatted = self.format_merged_messages(pending_messages)
                        if formatted:
                            conversation_content += formatted
                            message_count += 1
                        # Clear and start new accumulation
                        pending_messages = [msg_obj]

                # After reading entire file, output remaining messages
                if pending_messages:
                    formatted = self.format_merged_messages(pending_messages)
                    if formatted:
                        conversation_content += formatted
                        message_count += 1

        except Exception as e:
            print(f"    Error: Cannot read file {jsonl_path}: {e}")
            import traceback
            traceback.print_exc()
            return

        # Generate output filename
        output_filename = self.generate_filename(conversation_content, jsonl_name)
        output_path = output_dir / output_filename

        # Write to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(conversation_content)
            print(f"    ✓ Exported: {output_path} (total {message_count} messages)")
        except Exception as e:
            print(f"    Error: Cannot write to file {output_path}: {e}")

    def _format_message_header(self, role: str, timestamp: str) -> str:
        """
        Format message header

        Args:
            role: Role (user/assistant)
            timestamp: Timestamp

        Returns:
            Formatted header string
        """
        formatted_time = self.format_timestamp(timestamp)
        role_name = self.texts['user'] if role == 'user' else self.texts['assistant']
        output = f"\n{'─' * self.SEPARATOR_LENGTH}\n"
        output += f"{role_name} | {formatted_time}\n"
        output += f"{'─' * self.SEPARATOR_LENGTH}\n"
        return output

    def format_merged_messages(self, messages: list) -> str:
        """
        Format merged messages

        Args:
            messages: List of messages, each containing data, role, text, has_tools

        Returns:
            Formatted message string
        """
        if not messages:
            return ''

        # Use timestamp and role from first message
        first_msg = messages[0]
        role = first_msg['role']
        timestamp = first_msg['data'].get('timestamp', '')

        # Use unified header formatting method
        output = self._format_message_header(role, timestamp)

        # Merge content from all messages
        for i, msg in enumerate(messages):
            if msg['has_tools']:
                # For messages with tools, use original formatting logic
                # Add newline if previous is plain text
                if i > 0 and not messages[i-1]['has_tools']:
                    output += "\n"

                formatted = self.extract_message(msg['data'])
                if formatted:
                    # Remove duplicate headers (role, time, separator)
                    lines = formatted.split('\n')
                    # Skip first 4 lines (empty line, separator, role line, separator)
                    if len(lines) > 5:
                        output += '\n'.join(lines[5:])
            else:
                # Plain text message, add text directly
                output += msg['text']

        output += "\n\n"
        return output

    def _analyze_content(self, content: ContentData) -> ContentAnalysis:
        """
        Analyze content and extract text and tool information in a single pass

        Args:
            content: Message content

        Returns:
            Dictionary with keys: 'text' (str), 'has_tools' (bool)
        """
        result = {
            'text': '',
            'has_tools': False
        }

        if isinstance(content, str):
            result['text'] = self.clean_content(content)
            return result

        if not isinstance(content, list):
            return result

        text_parts = []
        has_tools = False

        for item in content:
            if not isinstance(item, dict):
                continue

            item_type = item.get('type', '')

            # Check for tools
            if item_type in ['tool_use', 'tool_result']:
                has_tools = True

            # Extract text content
            if item_type == 'text':
                text = item.get('text', '')
                if text:
                    text_parts.append(self.clean_content(text))

        result['text'] = '\n'.join(text_parts)
        result['has_tools'] = has_tools
        return result

    def _process_text_item(self, item: dict) -> tuple[str, bool]:
        """
        Process text content item

        Args:
            item: Content item dictionary

        Returns:
            Tuple of (formatted_text, has_content)
        """
        text_content = item.get('text', '')
        if text_content.strip():
            return self.clean_content(text_content), True
        return '', False

    def _process_tool_use_item(self, item: dict, is_first: bool) -> tuple[str, bool]:
        """
        Process tool use item

        Args:
            item: Tool use item dictionary
            is_first: Whether this is the first tool call

        Returns:
            Tuple of (formatted_text, has_content)
        """
        tool_name = item.get('name', '')
        # Add double newline before first tool, single before others
        newline = "\n\n" if is_first else "\n"
        output = f"{newline}{self.texts['tool']} {tool_name}\n"

        input_data = item.get('input')
        if input_data:
            output += f"{self.texts['param']} {self.format_dict(input_data)}\n"

        return output, True

    def _process_tool_result_item(self, item: dict) -> tuple[str, bool]:
        """
        Process tool result item

        Args:
            item: Tool result item dictionary

        Returns:
            Tuple of (formatted_text, has_content)
        """
        result_content = item.get('content', '')

        # Limit result content length
        if len(result_content) > self.MAX_RESULT_LENGTH:
            result_content = result_content[:self.MAX_RESULT_LENGTH] + "\n... (内容过长，已截断)\n"

        result_cleaned = self.clean_content(result_content)
        return f"\n{self.texts['result']}\n\n{result_cleaned}\n", True

    def _process_content_list(self, content: list) -> tuple[str, bool]:
        """
        Process content list and extract all meaningful items

        Args:
            content: List of content items

        Returns:
            Tuple of (formatted_content, has_valid_content)
        """
        content_parts = []
        is_first_tool = True

        for item in content:
            if not isinstance(item, dict):
                continue

            item_type = item.get('type', '')

            # Skip thinking items
            if item_type == 'thinking':
                continue

            # Process different item types
            if item_type == 'text':
                formatted, has_content = self._process_text_item(item)
                if has_content:
                    content_parts.append(formatted)
                    is_first_tool = True  # Reset after text content

            elif item_type == 'tool_use':
                formatted, has_content = self._process_tool_use_item(item, is_first_tool)
                if has_content:
                    content_parts.append(formatted)
                    is_first_tool = False

            elif item_type == 'tool_result':
                formatted, has_content = self._process_tool_result_item(item)
                if has_content:
                    content_parts.append(formatted)

        return ''.join(content_parts), len(content_parts) > 0

    def extract_message(self, data: Dict[str, Any]) -> str:
        """
        Extract and format message content

        Args:
            data: Message data dictionary

        Returns:
            Formatted message string
        """
        msg_type = data.get('type', '')
        message = data.get('message', {})
        timestamp = data.get('timestamp', '')

        # Only process user and assistant type messages
        if msg_type not in ['user', 'assistant']:
            return ''

        role = message.get('role', '')
        content = message.get('content', '')

        # Return empty string if content is None
        if content is None:
            return ''

        # Use unified header formatting method
        output = self._format_message_header(role, timestamp)

        # Process content based on type
        if isinstance(content, list):
            content_output, has_content = self._process_content_list(content)
        elif isinstance(content, str):
            cleaned_content = self.clean_content(content)
            has_content = bool(cleaned_content.strip())
            content_output = cleaned_content if has_content else ''
        else:
            has_content = False
            content_output = ''

        # Return empty string if no valid content
        if not has_content:
            return ''

        output += content_output
        output += "\n\n"
        return output

    def clean_content(self, content: Union[str, Any]) -> str:
        """
        Clean content format, remove line numbers, arrows, etc.

        Args:
            content: Raw content (string or convertible to string)

        Returns:
            Cleaned content string
        """
        if not content:
            return ''

        # Ensure content is string
        if not isinstance(content, str):
            content = str(content)

        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            # Remove line numbers and arrows (e.g., "     1→", "1→", "100  →")
            # Pattern: Line start space + number + optional space + arrow
            line = re.sub(r'^\s*\d+\s*→', '', line)

            # Remove other common tool output markers
            # E.g., "→" symbol appearing alone at line start
            line = re.sub(r'^→\s*', '', line)

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def format_timestamp(self, timestamp: str) -> str:
        """
        Format timestamp

        Args:
            timestamp: ISO 8601 format timestamp

        Returns:
            Formatted time string
        """
        if not timestamp:
            return ''

        # ISO 8601 format: 2025-12-30T02:53:40.140Z
        match = re.match(r'^(\d{4}-\d{2}-\d{2}T[\d:]+\.?\d*)(?:Z|([+-]\d{2}:\d{2}))?', timestamp)
        if match:
            return match.group(1)

        return timestamp

    def format_dict(self, data: Union[Dict, List, Any], indent: int = 0) -> str:
        """
        Format dictionary data into readable string

        Args:
            data: Data to format (dict, list, or other)
            indent: Indentation level

        Returns:
            Formatted string representation
        """
        if not isinstance(data, dict):
            return str(data)

        items = []
        for key in sorted(data.keys()):
            value = data[key]
            if isinstance(value, dict):
                items.append(f"{'  ' * indent}{key}: {self.format_dict(value, indent + 1)}")
            elif isinstance(value, list):
                items.append(f"{'  ' * indent}{key}: [{', '.join(str(v) for v in value)}]")
            else:
                items.append(f"{'  ' * indent}{key}: {value}")

        return '{' + ', '.join(items) + '}'

    def decode_project_name(self, encoded: str) -> str:
        """
        Decode encoded project directory name

        Args:
            encoded: Encoded project name (e.g., -home-user-work-...)

        Returns:
            Decoded path (e.g., /home/user/work/...)
        """
        # Convert -home-user-work-... format to /home/user/work/...
        decoded = encoded.lstrip('-')
        decoded = decoded.replace('-', '/')
        return decoded

    def _extract_meaningful_lines(self, content: str, max_lines: int = 2) -> List[str]:
        """
        Extract meaningful lines from content for filename generation

        Args:
            content: Conversation content
            max_lines: Maximum number of lines to extract

        Returns:
            List of meaningful text lines
        """
        lines = content.split('\n')
        meaningful_lines = []

        for line in lines:
            # Skip separator lines (─ or =)
            if re.match(r'^[─=]+$', line):
                continue

            # Skip role/user lines (👤, 🤖, 🔧, ✅)
            if re.match(r'^[👤🤖🔧✅]', line):
                continue

            # Skip timestamp and parameter lines
            if re.match(r'^\d{4}-\d{2}-\d{2}T[\d:]+', line):
                continue
            if re.match(r'^(参数|Args|Result|结果)', line):
                continue
            if line.strip().startswith('{'):
                continue

            # Collect meaningful text lines
            if re.search(r'\S', line) and len(line.strip()) > 3:
                clean_line = line.strip()
                # Remove leading marker characters
                clean_line = re.sub(r'^^[#\*\s-]+', '', clean_line)
                if len(clean_line) > 0:
                    meaningful_lines.append(clean_line)
                    if len(meaningful_lines) >= max_lines:
                        break

        return meaningful_lines

    def _clean_filename_text(self, text: str) -> str:
        """
        Clean text for use in filename

        Args:
            text: Text to clean

        Returns:
            Cleaned text containing only safe characters
        """
        # Keep only safe characters (Chinese, English, numbers, underscores, hyphens)
        return re.sub(r'[^\w\u4e00-\u9fa5_-]', '', text)

    def _truncate_filename_bytes(self, text: str, max_bytes: int) -> str:
        """
        Truncate text to fit within byte limit

        Args:
            text: Text to truncate
            max_bytes: Maximum bytes allowed

        Returns:
            Truncated text that fits within byte limit
        """
        # Truncate character by character until within limit
        while len(text.encode('utf-8')) > max_bytes and len(text) > 0:
            text = text[:-1]
        return text

    def generate_filename(self, content: str, original_name: str) -> str:
        """
        Generate output filename from content and original name

        Args:
            content: Conversation content
            original_name: Original filename

        Returns:
            Generated filename
        """
        # Extract base name from original (remove .jsonl extension)
        base_name = original_name.replace('.jsonl', '')

        # Extract meaningful lines from content
        meaningful_lines = self._extract_meaningful_lines(content, max_lines=2)

        # Join meaningful content with underscores
        meaningful_text = '_'.join(meaningful_lines)

        # Clean text to keep only safe characters
        meaningful_text = self._clean_filename_text(meaningful_text)

        # Truncate to fit within byte limit
        meaningful_text = self._truncate_filename_bytes(meaningful_text, self.MAX_FILENAME_BYTES)

        # Build final filename
        if meaningful_text:
            filename = f"{base_name}_{meaningful_text}.txt"
        else:
            filename = f"{base_name}.txt"

        return filename


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Claude Code 历史记录导出工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Supported languages:
  zh (中文), en (English), es (Español), fr (Français),
  de (Deutsch), ja (日本語), ko (한국어), ru (Русский),
  pt (Português), it (Italiano)

示例:
  %(prog)s                              # Use default settings (Chinese, output to ./output)
  %(prog)s --lang en                    # English interface (output to ./output)
  %(prog)s /path/to/output              # Specify output directory
  %(prog)s --lang ja /path/to/output    # Japanese interface and specify output directory
        '''
    )

    parser.add_argument(
        'output_dir',
        nargs='?',
        default='output',
        help='输出目录路径（默认：./output）'
    )

    parser.add_argument(
        'projects_dir',
        nargs='?',
        help='Claude projects 目录路径（默认：~/.claude/projects）'
    )

    parser.add_argument(
        '--lang',
        choices=list(LANGUAGES.keys()),
        default='zh',
        help='Interface language (default: zh Chinese)'
    )

    args = parser.parse_args()

    # Create exporter and execute export
    exporter = ClaudeHistoryExporter(
        projects_dir=args.projects_dir,
        output_dir=args.output_dir,
        lang=args.lang
    )
    exporter.export_all()


if __name__ == "__main__":
    main()
