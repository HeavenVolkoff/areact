# Internal
import typing as T
from collections import deque

# External
from aRx.abstract.namespace import Namespace

# Project
from ..stream import SingleStream

# Generic Types
K = T.TypeVar("K")


class Take(SingleStream[K]):
    def __init__(self, count: int, **kwargs: T.Any) -> None:
        super().__init__(**kwargs)

        self._count = abs(count)
        self._reverse_queue: T.Optional[T.Deque[T.Tuple[K, Namespace]]] = (
            deque(maxlen=self._count) if count < 0 else None
        )

    async def __asend__(self, value: K, namespace: Namespace) -> None:
        if self._reverse_queue is None:
            if self._count > 0:
                self._count -= 1
                awaitable: T.Awaitable[T.Any] = super().__asend__(value, namespace)
            else:
                awaitable = self.aclose()

            # Remove reference early to avoid keeping large objects in memory
            del value

            await awaitable
        else:
            self._reverse_queue.append((value, namespace))

    async def __aclose__(self) -> None:
        while self._reverse_queue:
            await super().__asend__(*self._reverse_queue.popleft())

        return await super().__aclose__()


__all__ = ("Take",)
