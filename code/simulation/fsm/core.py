__author__ = 'Benjamin'


class SimulationFSM(object):
    def __init__(self):
        self._states = dict()
        self._transitions = dict()
        self._env = None
        self.curState = State(self)
        """:type : State"""
        self.prevState = None
        """:type : State"""
        self.transition = None
        """:type : Transition"""

    @property
    def env(self):
        """
        :return: The environment of the simulation
        :rtype: simulation.environment.SimulationEnvironment
        """
        return self._env

    @env.setter
    def env(self, environment):
        self._env = environment

    def add_state(self, state_name, state):
        state.name = state_name
        self._states[state_name] = state

    def add_transition(self, trans_name, transition):
        transition.name = trans_name
        self._transitions[trans_name] = transition

    def set_state(self, state_name):
        self.prevState = self.curState
        self.curState = self._states[state_name]

    def set_transition(self, trans_name):
        self.transition = self._transitions[trans_name]

    def unlink(self):
        """Remove circular references to objects no longer required."""
        for state in self._states.values():
            state.unlink()
        self._states = None

    def execute(self):
        if self.transition is not None:
            self.curState.exit()
            self.transition.execute()
            self.set_state(self.transition.toState)
            self.curState.enter()
            self.transition = None
        self.curState.execute()


class State(object):
    def __init__(self, fsm):
        """
        Constructor
        :param fsm: The simulation's finite state machine
        :type fsm: SimulationFSM
        """
        self._fsm = fsm
        self._name = None

    @property
    def name(self):
        """
        :return: The name of the State
        :rtype: simulation.fsm.States
        """
        return self._name

    @name.setter
    def name(self, name):
        """
        :param name: Setter for the name
        :type name: simulation.fsm.States
        """
        self._name = name

    @property
    def fsm(self):
        """
        :return: Instance of the Finite State Machine
        :rtype: SimulationFSM
        """
        return self._fsm

    def unlink(self):
        """Remove circular references to objects no longer required."""
        self._fsm = None

    def enter(self):
        pass

    def execute(self):
        pass

    def exit(self):
        pass


class Transition(object):
    def __init__(self, to_state):
        """
        Constructor
        :param to_state:
        :type to_state: simulation.fsm.States
        """
        self.toState = to_state
        self._name = None
        self._data = dict()

    @property
    def name(self):
        """
        :return: The name of the Transition
        :rtype: simulation.fsm.Transitions
        """
        return self._name

    @name.setter
    def name(self, name):
        """
        :param name: Setter for the name
        :type name: simulation.fsm.Transitions
        """
        self._name = name

    def execute(self):
        pass
