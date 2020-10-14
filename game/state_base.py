import logging
from .state_machine_context import StateMachineContext

logger = logging.getLogger(__name__)


class StateBase:
    def __init__(self, context: StateMachineContext):
        self._context = context

    @property
    def name(self):
        return self.__class__.__name__

    def on_enter(self):
        logger.debug(f"{self}.on_enter()")

    @classmethod
    def create(cls, context, args):
        return cls(context, *args)

    def __str__(self):
        return self.name
