__author__ = 'Benjamin'


class SimulationFSM(object):
    def __init__(self):
        self._states = dict()
        self._transitions = dict()
        self.curState = None
        """:type : simulation.fsm.states.State"""
        self.prevState = None
        """:type : simulation.fsm.states.State"""
        self.transition = None
        """:type : simulation.fsm.transitions.Transition"""

    def add_state(self, stateName, state):
        self._states[stateName] = state

    def add_transition(self, transName, transition):
        self._transitions[transName] = transition

    def set_state(self, stateName):
        self.prevState = self.curState
        self.curState = self._states[stateName]

    def set_transition(self, transName):
        self.transition = self._transitions[transName]

    def execute(self):
        if self.transition is not None:
            self.curState.exit()
            self.transition.execute()
            self.set_state(self.transition.toState)
            self.curState.enter()
            self.transition = None
        self.curState.execute()


class State(object):
    def __init__(self, FSM):
        """

        :param FSM: The simulation's finite state machine
        :type FSM: simulation.fsm.fsm.SimulationFSM
        """
        self._fsm = FSM

    def enter(self):
        pass

    def execute(self):
        pass

    def exit(self):
        pass


class Transition(object):
    def __init__(self, toState):
        """

        :param toState:
        :type toState: simulation.fsm.states.State
        :return:
        """
        self.toState = toState

    def execute(self):
        pass
