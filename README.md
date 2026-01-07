# Claude Code History Exporter

A Python script to export Claude Code conversation history from JSONL format to human-readable text files.

## ✨ Features

1. **Multi-language Support** - 10 languages supported (zh, en, es, fr, de, ja, ko, ru, pt, it)
2. **Smart Message Merging** - Automatically merges consecutive messages from the same role
3. **Code Cleanup** - Removes line numbers and arrow markers from code blocks
4. **Chat-style Format** - Uses emojis for clean, readable output
5. **Code-friendly** - No indentation in tool results, easy to copy code
6. **Zero Dependencies** - Uses only Python standard library

## 🚀 Quick Start

```bash
# Basic usage (exports to ./output directory by default)
python3 main.py

# View exported files
ls output/
```

## 🌍 Supported Languages

```bash
# Chinese (default)
python3 main.py

# English
python3 main.py --lang en

# Japanese
python3 main.py --lang ja

# Korean
python3 main.py --lang ko

# Other languages: es, fr, de, ru, pt, it
```

## 📁 Output Directory Structure

```
output/
├── home-user--doter/
│   ├── xxx_first_content.txt
│   └── ...
├── home-user-cchistory/
│   └── ...
└── home-user-work-Code-Plus/
    └── ...
```

## 📝 Output Format Example

```
────────────────────────────────────────────────────────────────────────────────
👤 User | 2025-12-30T02:53:40.140
────────────────────────────────────────────────────────────────────────────────
Check if implementation matches design docs.

────────────────────────────────────────────────────────────────────────────────
🤖 Assistant | 2025-12-30T02:53:49.910
────────────────────────────────────────────────────────────────────────────────
I'll help you check the implementation.

🔧 Read
参数: {file_path: /home/user/.../design.md}

🔧 Read
参数: {file_path: /home/user/.../proto}


────────────────────────────────────────────────────────────────────────────────
👤 User | 2025-12-30T02:53:54.246
────────────────────────────────────────────────────────────────────────────────
✅ 结果:

syntax = "proto3";

package delivery.v1;
...
```

## 🔧 Advanced Usage

```bash
# Specify output directory
python3 main.py /path/to/output

# Specify both source and output directories
python3 main.py /output /path/to/.claude/projects

# Export in English to specific directory
python3 main.py --lang en /path/to/english/output

# View help
python3 main.py --help
```

## 📊 Features

### Smart Message Merging
- Consecutive messages from the same role are automatically merged
- Reduces repetitive header information
- Improves readability

### Code Cleanup
- Automatically removes line numbers and arrows (e.g., `1→`, `100  →`)
- Preserves original indentation
- Code ready to use directly

### File Naming
- Extracts key information from first few lines of conversation
- Uses underscores, no spaces
- Length limited to ~20 Chinese characters

## 🛠️ Technical Information

- **Python Version**: 3.6 or higher (tested on Python 3.6+)
- **Dependencies**: Standard library only (zero third-party dependencies)
- **Cross-platform**: Linux, macOS, Windows
- **Default Output**: `./output/`
- **File Encoding**: UTF-8

## 💡 Usage Tips

1. **Batch Export**: Run the script directly to export all projects automatically
2. **Backup**: Copy the entire `output/` directory for backup
3. **Search**: Exported text files can be easily searched
4. **Version Comparison**: Compare conversation records from different time periods

## 📦 File List

- `main.py` - Main script
- `README.md` - This file
- `LICENSE` - MIT License

## 🎯 Language Support

| Code | Language | Example |
|------|----------|---------|
| `zh` | 中文 | 👤 用户 / 🤖 助手 |
| `en` | English | 👤 User / 🤖 Assistant |
| `es` | Español | 👤 Usuario / 🤖 Asistente |
| `fr` | Français | 👤 Utilisateur / 🤖 Assistant |
| `de` | Deutsch | 👤 Benutzer / 🤖 Assistent |
| `ja` | 日本語 | 👤 ユーザー / 🤖 アシスタント |
| `ko` | 한국어 | 👤 사용자 / 🤖 어시스턴트 |
| `ru` | Русский | 👤 Пользователь / 🤖 Ассистент |
| `pt` | Português | 👤 Usuário / 🤖 Assistente |
| `it` | Italiano | 👤 Utente / 🤖 Assistente |

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

