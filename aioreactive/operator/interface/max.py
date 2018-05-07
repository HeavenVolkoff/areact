# Internal
import typing as T

# Project
from ..stream import SingleStream
from ..abstract import Observable, Observer, Disposable
from ..disposable import CompositeDisposable

K = T.TypeVar('K')


class Max(Observable):
    class Stream(SingleStream[K]):
        def __init__(self, **kwargs) -> None:
            super().__init__(**kwargs)
            self._max = None  # type: K

        async def __asend__(self, value: K) -> None:
            if value > self._max:
                self._max = value

        async def __close__(self) -> None:
            await super().__asend__(self._max)
            await super().__aclose__()

    def __init__(self, source: Observable, **kwargs) -> None:
        super().__init__(**kwargs)
        self._source = source

    async def __aobserve__(self, observer: Observer) -> Disposable:
        sink = Max.Stream()  # type: SingleStream[K]

        up = await self._source.__aobserve__(sink)
        down = await sink.__aobserve__(observer)

        return CompositeDisposable(up, down)


def max(source: Observable) -> Observable:
    """Project each item of the source stream.

    xs = max(source)

    Keyword arguments:
    source: Source to find max value from.

    Returns a stream with a single item that is the item with the
    maximum value from the source stream.
    """
    return Max(source)