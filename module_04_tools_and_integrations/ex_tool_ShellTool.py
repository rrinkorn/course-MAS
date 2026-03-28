from langchain_community.tools import ShellTool

shell = ShellTool()

# ОПАСНО! Это даёт полный доступ к shell
result = shell.invoke({"commands": "ls -la"})
print(result)