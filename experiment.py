"""Monte Carlo Markov Chains with people."""
import random
import time
from operator import attrgetter

from flask import Response
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from dallinger.bots import BotBase
from dallinger.experiment import Experiment, experiment_route
from dallinger.networks import Chain


class MCMCP(Experiment):
    """Define the structure of the experiment."""

    def __init__(self, session=None):
        """Call the same function in the super (see experiments.py in dallinger).

        The models module is imported here because it must be imported at
        runtime.

        A few properties are then overwritten.

        Finally, setup() is called.
        """
        super(MCMCP, self).__init__(session)
        from . import models

        self.models = models
        self.experiment_repeats = 2
        self.trials_per_participant = 20
        if session:
            self.setup()

    def create_node(self, network, participant):
        """Create a node for a participant."""
        return self.models.MCMCPAgent(network=network, participant=participant)

    def setup(self):
        """Setup the networks."""
        if not self.networks():
            super(MCMCP, self).setup()
            for net in self.networks():
                self.models.AnimalSource(network=net)
            self.session.commit()

    def create_network(self):
        """Create a new network."""
        return Chain(max_size=1000)

    def get_network_for_participant(self, participant):
        # human_nodes = Node.query.filter_by(participant_id=participant.id, human=True).all()
        human_chosen = [i for i in participant.nodes(failed="all") if i.human]
        if len(human_chosen) < self.trials_per_participant:
            return random.choice(self.networks())
        else:
            return None

    def add_node_to_network(self, node, network):
        """When a node is created it is added to the chain (see Chain in networks.py)
        and it receives any transmissions."""
        network.add_node(node)
        parent = node.neighbors(direction="from")[0]
        parent.transmit()
        node.receive()

    def data_check(self, participant):
        """Make sure each trial contains exactly one chosen info."""
        infos = participant.infos()
        return len([info for info in infos if info.chosen]) * 2 == len(infos)

    @experiment_route("/choice/<int:node_id>/<int:choice>/<int:human>", methods=["POST"])
    @classmethod
    def choice(cls, node_id, choice, human):
        from .models import Agent
        from dallinger import db

        try:
            exp = MCMCP(db.session)
            node = Agent.query.get(node_id)
            infos = node.infos()

            if choice == 0:
                info = min(infos, key=attrgetter("id"))
            elif choice == 1:
                info = max(infos, key=attrgetter("id"))
            else:
                raise ValueError("Choice must be 1 or 0")

            info.chosen = True

            if human == 1:
                info.human = True
                node.human = True
            elif human == 0:
                info.human = False
            else:
                raise ValueError("human must be 1 or 0")

            exp.save()

            return Response(status=200, mimetype="application/json")
        except Exception:
            return Response(status=403, mimetype="application/json")


class Bot(BotBase):
    """Bot tasks for experiment participation"""

    def participate(self):
        """Finish reading and send text"""
        try:
            while True:
                left = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "left_button"))
                )
                right = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "right_button"))
                )

                random.choice((left, right)).click()
                time.sleep(1.0)
        except TimeoutException:
            return False
