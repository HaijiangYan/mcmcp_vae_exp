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
from dallinger.models import Participant, Node

from datetime import datetime, timezone
from . import models
from math import ceil


class MCMCP(Experiment):
    """Define the structure of the experiment."""

    participant_constructor = models.Participant_with_timezone

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
        self.happy_chains = 68
        self.sad_chains = 68  # start here
        self.trials_per_participant = 600 + 12  # 500 trials plus 12 catch trials
        self.catch = [50, 250, 350, 500]  # after how many trials the catch trial occurs, which should not be the first trial in each block
        self.predict_1 = [35, 150, 380, 480]
        self.predict_2 = [80, 200, 420, 550]
        self.human_chosen = None
        if session:
            self.setup()

    def create_node(self, network, participant):
        """Create a node for a participant."""
        if self.human_chosen in self.catch + self.predict_1 + self.predict_2: 
            return self.models.Catcher(network=network, participant=participant)
        else:
            return self.models.MCMCPAgent(network=network, participant=participant)

    def setup(self):
        """Setup the networks."""
        if not self.networks():
            for i in range(self.happy_chains+2):
                network = self.create_network()
                network.role = f"happy_{int(ceil((i+1)/2))}"
                if i == self.happy_chains:
                    network = self.create_network()
                    network.role = "happy_predictor_1"
                if i == self.happy_chains+1:
                    network = self.create_network()
                    network.role = "happy_predictor_2"
                self.session.add(network)
            for i in range(self.sad_chains+2):
                network = self.create_network()
                network.role = f"sad_{int(ceil((i+1)/2))}"
                if i == self.sad_chains:
                    network = self.create_network()
                    network.role = "sad_predictor_1"
                if i == self.happy_chains+1:
                    network = self.create_network()
                    network.role = "sad_predictor_2"
                self.session.add(network)
            self.session.commit()

            for net in self.networks():
                if net.role[0] == 'h':
                    self.models.HappySource(network=net)
                else:
                    self.models.SadSource(network=net)
            self.session.commit()

    def create_network(self):
        """Create a new network."""
        return Chain(max_size=100000)

    def get_network_for_participant(self, participant):
        self.human_chosen = len([i for i in participant.nodes(failed="all") if i.human])
        if participant.id % 2 ==1:
            if self.human_chosen <= self.trials_per_participant // 2:
                if self.human_chosen in self.predict_1:
                    return random.choice(self.networks(role='happy_predictor_1'))
                elif self.human_chosen in self.predict_2:
                    return random.choice(self.networks(role='happy_predictor_2'))
                else:
                    return random.choice(self.networks(role=f'happy_{participant.id}'))
            elif self.human_chosen > self.trials_per_participant // 2 and self.human_chosen < self.trials_per_participant:
                if self.human_chosen in self.predict_1:
                    return random.choice(self.networks(role='sad_predictor_1'))
                elif self.human_chosen in self.predict_2:
                    return random.choice(self.networks(role='sad_predictor_2'))
                else:
                    return random.choice(self.networks(role=f'sad_{participant.id}'))
            else:
                return None
            
        else:
            if self.human_chosen <= self.trials_per_participant // 2:
                if self.human_chosen in self.predict_1:
                    return random.choice(self.networks(role='sad_predictor_1'))
                elif self.human_chosen in self.predict_2:
                    return random.choice(self.networks(role='sad_predictor_2'))
                else:
                    return random.choice(self.networks(role=f'sad_{participant.id}'))
            elif self.human_chosen > self.trials_per_participant // 2 and self.human_chosen < self.trials_per_participant:
                if self.human_chosen in self.predict_1:
                    return random.choice(self.networks(role='happy_predictor_1'))
                elif self.human_chosen in self.predict_2:
                    return random.choice(self.networks(role='happy_predictor_2'))
                else:
                    return random.choice(self.networks(role=f'happy_{participant.id}'))
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
        """Make sure each trial contains exactly one chosen info, if not, labeled as bad data and do another recruitment automatically."""
        infos = participant.infos()
        return len([info for info in infos if info.chosen]) > 0
        # return len([info for info in infos if info.chosen]) * 2 + len(self.catch) >= len(infos)

    @experiment_route("/choice/<int:node_id>/<int:choice>/<int:human>/<int:rt>", methods=["POST"])
    @classmethod
    def choice(cls, node_id, choice, human, rt):
        from .models import Agent
        from dallinger import db

        try:
            exp = MCMCP(db.session)
            node = Agent.query.get(node_id)
            infos = node.infos()

            if node.type == 'MCMCP_agent':
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
                    node.response_time = rt
                elif human == 0:
                    info.human = False
                else:
                    raise ValueError("human must be 1 or 0")

                exp.save()
                return Response(status=200, mimetype="application/json")
            elif node.type == 'Catcher':
                if choice == 0:
                    node.human = True
                    node.response_time = rt
                else: 
                    node.human = False
                    node.response_time = rt

                exp.save()
                return Response(status=200, mimetype="application/json")

        except Exception:
            return Response(status=403, mimetype="application/json")


    @experiment_route("/busy", methods=["GET"])
    @classmethod
    def anyone_working(cls):
        from .models import Participant
        from dallinger import db
        
        try:
            exp = MCMCP(db.session)
            anyone_working = Participant.query.filter_by(status = 'working').one_or_none()

            if anyone_working == None:
                return {'result': 0}
            else:
                if datetime.utcnow().replace(tzinfo=timezone.utc).timestamp() - float(anyone_working.utc) < 8400:
                    return {'result': 1}
                else:
                    anyone_working.status = 'submitted'
                    exp.save()
                    return {'result': 0}
            
        except Exception:
            return {'result': 1}


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






