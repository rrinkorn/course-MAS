# %%
"""Демонстрация защиты от path traversal."""
from langchain_community.agent_toolkits import FileManagementToolkit
import tempfile

workspace = tempfile.mkdtemp()

toolkit = FileManagementToolkit(
    root_dir=workspace,
    selected_tools=["read_file"]
)

read_tool = toolkit.get_tools()[0]

# Попытка выйти за пределы root_dir
result = read_tool.invoke({"file_path": "../../../etc/passwd"})

if "Access denied" in result or "Error" in result:
    print(f"✅ Защита работает: {result}")
else:
    print(f"⚠️ УЯЗВИМОСТЬ! Получен доступ: {result}")

import shutil
shutil.rmtree(workspace)