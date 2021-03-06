"""pipe

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T

# Project
from .sink_op import sink
from ..protocols import (
    ObserverProtocol,
    ObservableProtocol,
    TransformerProtocol,
    TransformerProtocolWithOperators,
)
from .observe_op import observe
from ..protocols.transformer_protocol import add_operators

if T.TYPE_CHECKING:
    # Internal
    from types import TracebackType


# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")
M = T.TypeVar("M")


class pipe(observe[K], T.Generic[K, L]):
    def __init__(
        self,
        observable: ObservableProtocol[K],
        transformer: TransformerProtocol[K, L],
        *,
        previous_pipe: T.Optional["pipe[M, K]"] = None,
        **kwargs: T.Any,
    ) -> None:
        super().__init__(observable, transformer, **kwargs)

        # Internal
        self._previous = previous_pipe
        self._transformer: TransformerProtocolWithOperators[K, L] = add_operators(transformer)

    def __or__(self, transformer: TransformerProtocol[L, M]) -> "pipe[L, M]":
        return pipe(self._transformer, transformer, previous_pipe=self)

    def __gt__(self, observer: ObserverProtocol[L]) -> sink[L]:
        return sink(self._transformer, observer, previous_pipe=self)

    def __await__(self) -> T.Generator[None, None, TransformerProtocolWithOperators[K, L]]:
        yield from super().__await__()
        return self._transformer

    async def __aenter__(self) -> TransformerProtocolWithOperators[K, L]:
        await super().__aenter__()

        if self._previous:
            await self._previous.__aenter__()

        return self._transformer

    async def __aexit__(
        self,
        exc_type: T.Optional[T.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional["TracebackType"],
    ) -> None:
        if self._previous is not None:
            await self._previous.__aexit__(exc_type, exc_value, traceback)

        await super().__aexit__(exc_type, exc_value, traceback)
