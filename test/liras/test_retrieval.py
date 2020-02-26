import os
import numpy as np

os.environ["LIRAS_PATH"] = "/home/simonpf/src/joint_flight"
os.environ["ARTS_DATA_PATH"] = "/home/simonpf/src/arts_xml"
os.environ["ARTS_BUILD_PATH"] = "/home/simonpf/build/arts_fast"

from parts.utils.data_providers import NetCDFDataProvider
import mcrf.liras.setup
import mcrf.liras
from   mcrf.retrieval        import CloudRetrieval
from   mcrf.sensors          import mwi, ici, lcpr
from   mcrf.liras  import snow, h2o_a_priori, cloud_water_a_priori
from   mcrf.liras.single_species import ice, rain
from   mcrf.liras.model_data import ModelDataProvider

import matplotlib.pyplot as plt
from IPython import get_ipython
ip = get_ipython()
if not ip is None:
    ip.magic("%load_ext autoreload")
    ip.magic("%autoreload 2")

#
# Input data.
#

filename = os.path.join(mcrf.liras.liras_path, "data", "forward_simulations_a_noise.nc")
offsets = {"a" : 3000,
           "b" : 2200}
scene = filename.split("_")[-2]
offset = offsets[scene]
observations = NetCDFDataProvider(filename)
observations.add_offset("profile", -offset)
shape = "LargePlateAggregate"

#
# Create the data provider.
#

ip = offset + 655
data_provider = ModelDataProvider(99,
                                  ice_psd    = ice.psd,
                                  snow_psd   = snow.psd,
                                  scene = scene.upper())
#
# Define hydrometeors and sensors.
#

#hydrometeors = [snow, ice, rain]
hydrometeors = [ice, rain]
sensors      = [lcpr, mwi, ici]

#
# Add a priori providers.
#

observation_error = mcrf.liras.ObservationError(sensors,
                                                forward_model_error = False,
                                                scene = scene)

data_provider.add(ice.a_priori[0])
data_provider.add(ice.a_priori[1])
data_provider.add(snow.a_priori[0])
data_provider.add(snow.a_priori[1])
data_provider.add(rain.a_priori[0])
data_provider.add(rain.a_priori[1])
data_provider.add(h2o_a_priori)
data_provider.add(cloud_water_a_priori)
data_provider.add(observation_error)
data_provider.add(observations)


#
# Run the retrieval.
#

retrieval = CloudRetrieval(hydrometeors, sensors, data_provider)
retrieval.setup()
retrieval.run(ip)

#
# Evaluate results.
#

ws = retrieval.simulation.workspace
r = retrieval.simulation.retrieval
rqs = r.retrieval_quantities
