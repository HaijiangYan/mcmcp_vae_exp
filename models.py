import random
from numpy.random import multivariate_normal
from numpy import dot
import json
from sqlalchemy import Boolean
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import cast

from dallinger.models import Info
from dallinger.models import Transformation
from dallinger.nodes import Agent
from dallinger.nodes import Source


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


class AnimalSource(Source):
    """A source that transmits animal shapes."""

    __mapper_args__ = {"polymorphic_identity": "animal_source"}

    def create_information(self):
        """Create a new Info.

        transmit() -> _what() -> create_information().
        """
        return AnimalInfo(origin=self, contents=None)


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

    properties = {
        "x": [-5.0, 5.0],
        "y": [-5.0, 5.0],
        "z": [-5.0, 5.0],
    }

    def __init__(self, origin, contents=None, **kwargs):
        if contents is None:
            data = {}
            for prop, prop_range in self.properties.items():
                data[prop] = random.uniform(prop_range[0], prop_range[1])
            contents = json.dumps(data)

        super(AnimalInfo, self).__init__(origin, contents, **kwargs)

    happy_cov_mat = [
        [0.23980569, 0.03504322, 0.06949917], 
        [0.03504322, 0.18401163, 0.09870955], 
        [0.06949917, 0.09870955, 0.24646653]
        ]
    happy_prop_cov = (happy_cov_mat / 2) * (2.38 * 2.38 / 3)  # estimated covariance fxgx multiplied by the scale factor

    def perturbed_contents(self):
        """Perturb the given animal."""
        animal = json.loads(self.contents)

        rand = random.uniform(0, 1)
        if rand >= 0.1:
            proposal = multivariate_normal([animal['x'], animal['y'], animal['z']], self.happy_prop_cov, 1)
            for n, prop in enumerate(animal.keys()):
                animal[prop] = proposal[0, n]
        else:
            for prop, prop_value in animal.items():
                jittered = random.uniform(-5, 5)  # 10% uniform proposal
                animal[prop] = jittered

        return json.dumps(animal)


class Perturbation(Transformation):
    """A perturbation is a transformation that perturbs the contents."""

    __mapper_args__ = {"polymorphic_identity": "perturbation"}
