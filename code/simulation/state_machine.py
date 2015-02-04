class StateMachine:
    def __init__(self, initial_state):
        self.currentState = initial_state
        self.currentState.run()

    def runAll(self, inputs):
        """Template Method"""
        for i in inputs:
            self.currentState = self.currentState.next(i)
            self.currentState.run()
