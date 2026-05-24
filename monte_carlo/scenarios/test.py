from ..runner import Scenario, MonteCarloResult

class TestScenario(Scenario):

    def run_once(self) -> Dict[str, int]:
        return {"value": 100}
