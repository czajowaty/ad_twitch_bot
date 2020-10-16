from game.state_base import StateBase
from game import commands


class StateElevatorEvent(StateBase):
    def on_enter(self):
        self._context.add_response(
            f"You found an elevator. You are currently on {self._context.floor + 1}F. "
            "Do you want to go to the next floor?")


class StateGoUp(StateBase):
    def on_enter(self):
        self._context.floor += 1
        self._context.generate_action(commands.ENTERED_NEXT_FLOOR)


class StateElevatorOmitted(StateBase):
    def on_enter(self):
        self._context.add_response("You omit elevator and stay ")
        self._context.generate_action(commands.EVENT_FINISHED)


class StateNextFloor(StateBase):
    def on_enter(self):
        floor = self._context.floor + 1
        if self._context.floor < self.game_config.highest_floor:
            self._context.add_response(f"You entered {floor}F.")
            self._context.generate_action(commands.EVENT_FINISHED)
        else:
            self._context.add_response(
                f"You have conquered the Tower! Congratulations! You receive 300 channel points.")
            self._context.generate_action(commands.RESTART)
