class StateMachine:
    def __init__(self, initial_state):
        self._currentState = initial_state

    @property
    def state(self):
        """Current state of the state machine
        :rtype: simulation.state.CommuterState
        :return: the current state of the state machine
        """
        return self._currentState

    @state.setter
    def state(self, next_state):
        """Set the next state for the state machine

        :param next_state: the next state that is executed
        :type next_state: simulation.state.CommuterState
        """
        self._currentState = next_state

    def runAll(self, inputs):
        """Template Method"""
        for i in inputs:
            self._currentState = self._currentState.next(i)
            self._currentState.run()