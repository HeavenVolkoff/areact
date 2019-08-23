# Internal
import typing as T

# External
import typing_extensions as Te

# External
from async_tools import attempt_await

# Project
from ..namespace import Namespace
from ..streams.single_stream import SingleStreamBase

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")


def noop(x: L) -> L:
    return x


class Map(SingleStreamBase[K, L]):
    @T.overload
    def __init__(
        self,
        asend_mapper: T.Callable[[L], T.Union[K, T.Awaitable[K]]],
        araise_mapper: T.Optional[
            T.Callable[[Exception], T.Union[Exception, T.Awaitable[Exception]]]
        ] = None,
        *,
        with_index: Te.Literal[False] = False,
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend_mapper: Te.Literal[None],
        araise_mapper: T.Callable[[Exception], T.Union[Exception, T.Awaitable[Exception]]],
        *,
        with_index: Te.Literal[False] = False,
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend_mapper: T.Callable[[L, int], T.Union[K, T.Awaitable[K]]],
        araise_mapper: T.Optional[
            T.Callable[[Exception], T.Union[Exception, T.Awaitable[Exception]]]
        ] = None,
        *,
        with_index: Te.Literal[True] = True,
        **kwargs: T.Any,
    ) -> None:
        ...

    def __init__(
        self,
        asend_mapper: T.Any = None,
        araise_mapper: T.Any = None,
        *,
        with_index: bool = False,
        **kwargs: T.Any,
    ) -> None:
        super().__init__(**kwargs)

        assert asend_mapper or araise_mapper

        self._index = 0 if with_index else None
        self._asend_mapper = noop if asend_mapper is None else asend_mapper
        self._araise_mapper = noop if araise_mapper is None else araise_mapper

    async def _asend_impl(self, value: L) -> K:
        if self._index is None:
            awaitable = self._asend_mapper(value)
        else:
            awaitable = self._asend_mapper(value, self._index)
            self._index += 1

        result = attempt_await(awaitable)

        # Remove reference early to avoid keeping large objects in memory
        del value

        return await result

    async def _athrow(self, exc: Exception, namespace: Namespace) -> bool:
        return await super()._athrow(await attempt_await(self._araise_mapper(exc)), namespace)


__all__ = ("Map",)
