"""
FileManagementToolkit — безопасная работа с файлами.

Ключевое: root_dir ограничивает агента только этой директорией!
"""
# Создаём временную рабочую директорию
import tempfile

from langchain_community.agent_toolkits import FileManagementToolkit

workspace = tempfile.mkdtemp(prefix="agent_workspace_")

toolkit = FileManagementToolkit(
    root_dir=workspace,
    selected_tools=[  # Выбираем только нужные операции
        "read_file",
        "write_file",
        "list_directory",
        "file_search",
    ],
    # Не включаем delete_file, move_file, copy_file — минимум привилегий!
)

tools = toolkit.get_tools()
print(f"Доступные инструменты: {[t.name for t in tools]}")

# Демонстрация использования
write_tool = next(t for t in tools if t.name == "write_file")
read_tool = next(t for t in tools if t.name == "read_file")
list_tool = next(t for t in tools if t.name == "list_directory")

# Записываем файл
write_tool.invoke({"file_path": "test.txt", "text": "Hello from AI Agent!"})

# Читаем файл
content = read_tool.invoke({"file_path": "test.txt"})
print(f"Содержимое файла: {content}")

# Список файлов
files = list_tool.invoke({"dir_path": "."})
print(f"Файлы в директории: {files}")

# Очистка
import shutil

shutil.rmtree(workspace)

print(toolkit)
