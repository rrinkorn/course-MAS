import docker

# %%
def run_code_in_sandbox(code: str, timeout: int = 30) -> str:
    client = docker.from_env()

    try:
        container = client.containers.run(
            "python:3.12-slim",
            command=["python", "-c", code],
            detach=True,            # запускаем в фоне
            mem_limit="256m",
            cpu_period=100000,
            cpu_quota=50000,
            network_disabled=True,
        )

        exit_code = container.wait(timeout=timeout)
        logs = container.logs().decode("utf-8")
        container.remove()

        if exit_code["StatusCode"] != 0:
            return f"Ошибка выполнения (код {exit_code['StatusCode']}):\n{logs}"
        return logs

    except Exception as e:
        # если таймаут — убиваем контейнер
        try:
            container.kill()
            container.remove()
        except Exception:
            pass
        return f"Ошибка: {str(e)}"

# %%
if __name__=="__main__":
    result = run_code_in_sandbox("print(2 + 2)")
    print(result)