"""
测试通过 obj.attr 和 await async_run(lambda: obj.attr) 性能差别

测试结果：十万次 obj.attr 花费时间是毫秒级，而后者是秒级(10 秒左右)。
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
