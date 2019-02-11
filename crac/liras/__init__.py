import os
from crac.psd import D14Ice, D14Liquid
from parts.retrieval.a_priori import *
from parts.jacobian import Atanh

liras_path = os.environ("LIRAS_PATH")
scattering_data = os.path.join(liras_path, "data", "scattering")

################################################################################
# Ice particles
################################################################################

ice_shape      = os.path.join(scattering_data, "8-ColumnAggregate.xml")
ice_shape_meta = os.path.join(scattering_data, "8-ColumnAggregate.meta.xml")

ice_mask       = And(TropopauseMask(), TemperatureMask(0.0, 273.0))
ice_covariance = Thikhonov(scaling = 1.0, mask = ice_mask)
ice_md_a_priori = FixedAPriori("ice_md", 1e-6, ice_covariance)

z_grid = np.np.linspace(0, 20, 11)
ice_n0_a_priori = FixedAPriori("ice_n0", 1e10, ice_covariance)
ice_n0_a_priori = ReducedVerticalGrid(ice_n0_a_priori, z_grid, "altitude")

ice = Hydrometeor("ice",
                  D14Ice(),
                  [ice_md_a_priori, ice_n0_a_priori],
                  ice_shape,
                  ice_shape_meta)

################################################################################
# Liquid particles
################################################################################

liquid_shape      = os.path.join(scattering_data, "LiquidSphere.xml")
liquid_shape_meta = os.path.join(scattering_data, "LiquidSphere.meta.xml")

liquid_mask  = TemperatureMask(240, 340.0)
liquid_covariance = Thikhonov(scaling = 1.0, mask = liquid_mask)
liquid_md_a_priori = FixedAPriori("liquid_md", 1e-6, liquid_covariance)

z_grid = np.np.linspace(0, 12, 7)
liquid_n0_a_priori = FixedAPriori("liquid_n0", 1e5, liquid_covariance)
liquid_n0_a_priori = ReducedVerticalGrid(liquid_n0_a_priori, z_grid, "altitude")

liquid = Hydrometeor("liquid",
                     D14Liquid(),
                     [liquid_md_a_priori, liquid_n0_a_priori],
                     liquid_shape,
                     liquid_shape_meta)

################################################################################
# Humidity
################################################################################

def a_priori_shape(t):
    t = Atanh()
    x = np.maximum(np.minimum(0.5 - (270 - t) / 100.0, 0.5), 0.0)
    return t(x)


rh_mask = TropopauseMask()
rh_covariance = Thikhonov(scaling = 1.0, mask = rh_mask)
rh_a_priori = FunctionalApriori("H2O", "temperature", a_priori_shape,
                                rh_covariance)

################################################################################
# Observation error
################################################################################

class ObservationError(DataProviderBase):
    """
    Observation error covariance matrix provider for the LIRAS study.

    This class works in the same way as the :class:`SensorNoiseAPriori` class
    parts, which means that it takes the :code:`nedt` attributes of the given
    sensors and concatenates these vectors into a combined diagonal matrix.

    In addition to that, however, this class also reads in estimated footprint
    error covariance matrices for LCPR and forward model error covariances
    that are included in the observation error covariance matrix, if the
    corresponding flags are set.

    The class assumes the existence of the following files in the :code:`data`
    subfolder of the LIRAS base directory :code:`LIRAS_PATH`:

        - :code:`covmat.npy`: The estimated covariance matrix of the
          footprint error for the LCPR sensor.

        - :code:`nedt_<sensor.name>_fm.npy`: Vector of estimated
          :math:`NE \Delta T` values for sensors in :code:`sensors`.
    """
    def __init__(self, sensors, footprint_error = False, forward_model_error = False):
        """
        Arguments:
            sensors(:code:`list`): List of :code:`parts.sensor.Sensor` objects
                containing the sensors that are used in the retrieval.

            footprint_error(:code:`Bool`): Include footprint error for :code:`lcpr`
                sensor.

            forward_model_error(:code:`Bool`): Include estimated model error for
                all sensors.

        """
        self.sensors = sensors
        self.fpe     = footprint_error
        self.fme     = forward_model_error

        liras_path = os.environ["LIRAS_PATH"]
        filename = os.path.join(liras_path, "data", "covmat.npy")
        self.lcpr_covmat =  np.load(os.path.join(filename))

        self.nedt_fm = {}
        for n in [s.name for s in sensors]:
            filename = os.path.join(liras_path, "data", "nedt_" + n + "_fm.npy")
            self.nedt_fm[n] = np.load(filename)

        self.noise_scaling = dict([(s.name, 1.0) for s in sensors])


    def get_observation_error_covariance(self, i_p):
        m = 0

        diag = []

        for s in self.sensors:
            c = self.noise_scaling[s.name]
            if isinstance(s, ActiveSensor):
                if s.name == "lcpr":
                    i_lcpr = sum([v.size for v in diag])
                    j_lcpr = i_lcpr + s.nedt.size
                diag += [(c * s.nedt) ** 2]

                if self.fme and not self.fpe:
                    diag[-1] += self.nedt_fm[s.name] ** 2

        for s in self.sensors:
            c = self.noise_scaling[s.name]
            if isinstance(s, PassiveSensor):
                diag += [(c * s.nedt) ** 2]

                if self.fme:
                    diag[-1] += self.nedt_fm[s.name] ** 2

        diag = np.concatenate(diag).ravel()

        covmat = sp.sparse.diags(diag, format = "coo")

        if self.fpe:
            covmat = covmat.todense()
            covmat[i_lcpr : j_lcpr, i_lcpr : j_lcpr] += self.lcpr_covmat

        return covmat
