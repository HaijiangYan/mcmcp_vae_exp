import random
from numpy.random import multivariate_normal
from numpy import array
import json
from sqlalchemy import Boolean
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import cast

from dallinger.models import Info
from dallinger.models import Transformation
from dallinger.models import Participant
from dallinger.nodes import Agent
from dallinger.nodes import Source

from datetime import datetime, timezone


class Participant_with_timezone(Participant):
    __mapper_args__ = {"polymorphic_identity": "ppt_p1_utc"}

    @hybrid_property
    def utc(self):
        """Use property1 to store whether a chosen info was by human (True-human)."""
        try:
            return str(self.property1)
        except TypeError:
            return None

    @utc.setter
    def utc(self, utc):
        """Assign human to property1."""
        self.property1 = repr(utc)

    @utc.expression
    def utc(self):
        """Retrieve human via property1."""
        return cast(self.property1, str)

    def __init__(self, recruiter_id, worker_id, assignment_id, hit_id, mode, fingerprint_hash=None, entry_information=None):
        super().__init__(recruiter_id, worker_id, assignment_id, hit_id, mode, fingerprint_hash, entry_information)
        # self.utc = datetime.utcnow()
        ts = datetime.utcnow().replace(tzinfo=timezone.utc).timestamp()
        self.utc = ts



class MCMCPAgent(Agent):

    __mapper_args__ = {"polymorphic_identity": "MCMCP_agent"}

    def update(self, infos):
        info = infos[0]
        self.replicate(info)
        new_info = AnimalInfo(origin=self, contents=info.perturbed_contents())
        Perturbation(info_in=info, info_out=new_info)

    def _what(self):
        infos = self.infos()
        return [i for i in infos if i.chosen][0]

    # Node-Property1
    @hybrid_property
    def human(self):
        """Use property1 to store whether a chosen info was by human (True-human)."""
        try:
            return bool(self.property1)
        except TypeError:
            return None

    @human.setter
    def human(self, human):
        """Assign human to property1."""
        self.property1 = repr(human)

    @human.expression
    def human(self):
        """Retrieve human via property1."""
        return cast(self.property1, Boolean)

    # Node-property2
    @hybrid_property
    def response_time(self):
        """Use property2 to store RT."""
        try:
            return int(self.property2)
        except TypeError:
            return None

    @response_time.setter
    def response_time(self, response_time):
        """Assign response_time to property2."""
        self.property2 = repr(response_time)

    @response_time.expression
    def response_time(self):
        """Retrieve RT via property2."""
        return cast(self.property2, int)

    @hybrid_property
    def cat(self):
        """Use property3 to store whether one is focused."""
        try:
            return bool(self.property3)
        except TypeError:
            return None

    @cat.setter
    def cat(self, cat):
        """Assign focus to property3."""
        self.property3 = repr(cat)

    @cat.expression
    def cat(self):
        """Retrieve human via property3."""
        return cast(self.property3, Boolean)


class Catcher(Agent):

    __mapper_args__ = {"polymorphic_identity": "Catcher"}

    def update(self, infos):
        info = infos[0]
        self.replicate(info)

    def _what(self):
        infos = self.infos()
        return infos[0]

    @hybrid_property
    def human(self):
        """Use property3 to store whether one is focused."""
        try:
            return bool(self.property1)
        except TypeError:
            return None

    @human.setter
    def human(self, human):
        """Assign focus to property3."""
        self.property1 = repr(human)

    @human.expression
    def human(self):
        """Retrieve human via property3."""
        return cast(self.property1, Boolean)

    # Node-property2
    @hybrid_property
    def response_time(self):
        """Use property2 to store RT."""
        try:
            return int(self.property2)
        except TypeError:
            return None

    @response_time.setter
    def response_time(self, response_time):
        """Assign response_time to property2."""
        self.property2 = repr(response_time)

    @response_time.expression
    def response_time(self):
        """Retrieve RT via property2."""
        return cast(self.property2, int)


class HappySource(Source):
    """A source that transmits happy face."""

    __mapper_args__ = {"polymorphic_identity": "happy_source"}

    def create_information(self):
        """Create a new Info.

        transmit() -> _what() -> create_information()
        """
        return AnimalInfo(origin=self, contents=None, start_point='happy')


class SadSource(Source):
    """A source that transmits sad face."""

    __mapper_args__ = {"polymorphic_identity": "sad_source"}

    def create_information(self):
        """Create a new Info.

        transmit() -> _what() -> create_information()
        """
        return AnimalInfo(origin=self, contents=None, start_point='sad')


class AnimalInfo(Info):
    """An Info that can be chosen."""

    __mapper_args__ = {"polymorphic_identity": "vector_info"}

    @hybrid_property
    def chosen(self):
        """Use property1 to store whether an info was chosen."""
        try:
            return bool(self.property1)
        except TypeError:
            return None

    @chosen.setter
    def chosen(self, chosen):
        """Assign chosen to property1."""
        self.property1 = repr(chosen)

    @chosen.expression
    def chosen(self):
        """Retrieve chosen via property1."""
        return cast(self.property1, Boolean)

    @hybrid_property
    def human(self):
        """Use property2 to store whether a chosen info was by human (True-human)."""
        try:
            return bool(self.property2)
        except TypeError:
            return None

    @human.setter
    def human(self, human):
        """Assign human to property2."""
        self.property2 = repr(human)

    @human.expression
    def human(self):
        """Retrieve human via property2."""
        return cast(self.property2, Boolean)

    # happy center: [ 1.57248022 -0.99373547 -0.14020095]
    # sad center: [-0.89223572  0.6654995   0.58393501]
    happy_start = {
        "x": 1.57248022,
        "y": -0.99373547,
        "z": -0.14020095,
    }
    sad_start = {
        "x": -0.89223572,
        "y": 0.6654995,
        "z": 0.58393501,
    }

    def __init__(self, origin, contents=None, start_point='happy', **kwargs):
        if contents is None:
            data = {}
            if start_point == 'happy':
                for prop, prop_range in self.happy_start.items():
                    data[prop] = random.uniform(prop_range - 0.5, prop_range + 0.5)
            elif start_point == 'sad':
                for prop, prop_range in self.sad_start.items():
                    data[prop] = random.uniform(prop_range - 0.5, prop_range + 0.5)
            contents = json.dumps(data)

        super(AnimalInfo, self).__init__(origin, contents, **kwargs)

    prop_cov = array([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]
        ])  # estimated covariance fxgx multiplied by the scale factor

    def perturbed_contents(self):
        """Perturb the given animal."""
        animal = json.loads(self.contents)

        # rand = random.uniform(0, 1)
        # if rand >= 0.1:
        if self.network_id <= 70:
            proposal = multivariate_normal([animal['x'], animal['y'], animal['z']], self.prop_cov * 1.8, 1)
        else:
            proposal = multivariate_normal([animal['x'], animal['y'], animal['z']], self.prop_cov * 1.4, 1)
        for n, prop in enumerate(animal.keys()):
            animal[prop] = proposal[0, n]
        # else:
            # for prop, prop_value in animal.items():
                # jittered = random.uniform(-5, 5)  # 10% uniform proposal
                # animal[prop] = jittered
        return json.dumps(animal)


class Perturbation(Transformation):
    """A perturbation is a transformation that perturbs the contents."""

    __mapper_args__ = {"polymorphic_identity": "perturbation"}
