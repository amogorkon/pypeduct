from __future__ import annotations

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


def test_async_function_pipe():
    @pyped
    async def async_pipeline(x):
        return x >> (lambda v: v + 1)

    async def run_async_pipeline():
        return await async_pipeline(5)

    assert asyncio.run(run_async_pipeline()) == 6  # 5 + 1 = 6


def test_async_for_loop_pipeline():
    @pyped
    async def async_for_loop_pipeline(x):
        results = []
        async for i in async_number_generator(3):
            results.append(i)
        return x >> (lambda val: results)

    async def run_async_for_loop_pipeline():
        return await async_for_loop_pipeline(5)

    async def async_number_generator(n):  # Define generator within test for scope
        for i in range(n):
            await asyncio.sleep(0.01)
            yield i

    assert asyncio.run(run_async_for_loop_pipeline()) == [
        0,
        1,
        2,
    ]
