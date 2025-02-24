import asyncio

from pypeduct.pyping import pyped


def test_async_pipe():
    @pyped
    async def async_func() -> int:
        result: int = 10 >> (lambda x: x * 2)
        return result

    result = asyncio.run(async_func())
    assert result == 20


def test_pipe_with_async_generator():
    @pyped
    async def async_generator_pipe() -> list[int]:
        async def async_gen():
            for i in range(3):
                yield i

        result: list[int] = [i async for i in async_gen()] >> list
        return result

    result = asyncio.run(async_generator_pipe())
    assert result == [0, 1, 2]


def test_await_in_pipe():
    @pyped
    async def await_pipe() -> str:
        async def async_upper(s: str) -> str:
            await asyncio.sleep(0.1)
            return s.upper()

        return await ("hello" >> async_upper)

    result = asyncio.run(await_pipe())
    assert result == "HELLO"
