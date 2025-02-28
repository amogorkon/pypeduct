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


def test_awaitable_in_pipeline():
    async def awaitable_func(x):
        await asyncio.sleep(0.01)
        return x + 1

    @pyped
    async def awaitable_pipeline(x):
        return x >> awaitable_func

    async def run_awaitable_pipeline():
        return await awaitable_pipeline(5)

    assert asyncio.run(run_awaitable_pipeline()) == 6  # Awaitable function in pipeline


def test_async_lambda_in_pipeline():
    @pyped
    async def async_lambda_pipeline(x):
        return x >> (
            lambda val: asyncio.sleep(0.01) or val + 1
        )  # Async lambda (returning awaitable)

    async def run_async_lambda_pipeline():
        return await async_lambda_pipeline(5)

    assert asyncio.run(run_async_lambda_pipeline()) == 6  # Async lambda in pipeline


def test_async_comprehension_pipeline():
    @pyped
    async def async_comprehension_pipeline():
        return [await asyncio.sleep(0.01) or i * 2 async for i in range(3)] >> (
            lambda x: sum(x)
        )

    async def run_async_comprehension_pipeline():
        return await async_comprehension_pipeline()

    assert (
        asyncio.run(run_async_comprehension_pipeline()) == 6
    )  # Async comprehension as initial value


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
    ]  # Async for loop in pipeline


def test_async_with_statement_pipeline():
    class AsyncContextManager:
        async def __aenter__(self):
            print("Entering async context")
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            print("Exiting async context")

        async def process(self, x):
            await asyncio.sleep(0.01)
            return x + 1

    @pyped
    async def async_with_statement_pipeline(x):
        async with AsyncContextManager() as acm:
            return x >> acm.process

    async def run_async_with_statement_pipeline():
        return await async_with_statement_pipeline(5)

    assert (
        asyncio.run(run_async_with_statement_pipeline()) == 6
    )  # Async with statement in pipeline
