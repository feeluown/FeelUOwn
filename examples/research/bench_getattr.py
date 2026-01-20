"""
Testing the performance difference between accessing `obj.attr` directly and using `await async_run(lambda: obj.attr)`.

Test results: accessing `obj.attr` 100,000 times takes milliseconds, whereas the latter takes seconds (around 10 seconds).
"""


import asyncio
import time


class Obj:
    def __init__(self):
        self.attr = 1

    @property
    def prop(self):
        return 1


async def f():
    loop = asyncio.get_event_loop()
    obj = Obj()

    t = time.time()
    t_cpu = time.process_time()

    for _ in range(0, 100000):
        await loop.run_in_executor(None, lambda: obj.attr)

    print(time.time() - t )
    print(time.process_time() - t_cpu)



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(f())
