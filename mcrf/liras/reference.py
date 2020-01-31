"""
Defines a priori assumptions for the reference cost calculation for the
 combined retrieval.

The reference calculations use the reference hydrometeor concentrations from
the model data to provide an upper bound on the minimum achievable retrieval
cost.

Attributes:

     ice: Hydrometeor and a priori definition for frozen hydrometeors.

     rain: Hydrometeor and a priori definition for liquid hydrometeors.

     h2o_a_priori: A priori for humidity retrieval.

     cloud_water_a_priori: A priori for liquid cloud retrieval.
"""
import os
import numpy as np
from mcrf.psds                import D14NDmIce, D14NDmLiquid
from mcrf.hydrometeors        import Hydrometeor
from parts.retrieval.a_priori import *
from parts.scattering.psd     import Binned
from parts.jacobian           import Atanh, Log10, Identity, Composition

liras_path = os.environ["LIRAS_PATH"]
scattering_data = os.path.join(liras_path, "data", "scattering")

################################################################################
# Ice particles
################################################################################

def n0_a_priori(t):
    t = t - 272.15
    return np.log10(np.exp(-0.076586 * t + 17.948))

def dm_a_priori(t):
    n0 = 10 ** n0_a_priori(t)
    iwc = 1e-6
    dm = (4.0 ** 4 * iwc / (np.pi * 917.0)  / n0) ** 0.25
    return dm

ice_shape      = os.path.join(scattering_data, "8-ColumnAggregate.xml")
ice_shape_meta = os.path.join(scattering_data, "8-ColumnAggregate.meta.xml")
ice_mask       = And(AltitudeMask(0.0, 19e3), TemperatureMask(0.0, 276.0))

ice_covariance  = Diagonal(100e-6 ** 2, mask = ice_mask, mask_value = 1e-12)
ice_covariance  = SpatialCorrelation(ice_covariance, 2e3, mask = ice_mask)
ice_dm_a_priori = FunctionalAPriori("ice_dm", "temperature", dm_a_priori, ice_covariance,
                                    mask = ice_mask, mask_value = 1e-8)
ice_dm_a_priori = ReferenceAPriori("ice_dm", ice_covariance, mask = ice_mask, mask_value = 1e-8,
                                   a_priori = ice_dm_a_priori, transformation = Identity())

ice_covariance  = Diagonal(0.25, mask = ice_mask, mask_value = 1e-12)
ice_covariance  = SpatialCorrelation(ice_covariance, 4e3, mask = ice_mask)
ice_n0_a_priori = FunctionalAPriori("ice_n0", "temperature", n0_a_priori, ice_covariance,
                                    mask = ice_mask, mask_value = 2)
ice_n0_a_priori = ReferenceAPriori("ice_n0", ice_covariance, mask = ice_mask, mask_value = 2,
                                   a_priori = ice_n0_a_priori,
                                   transformation = Log10())
ice_n0_a_priori = MaskedRegularGrid(ice_n0_a_priori, 10, ice_mask, "altitude", provide_retrieval_grid = False)

ice = Hydrometeor("ice", D14NDmIce(), [ice_n0_a_priori, ice_dm_a_priori], ice_shape, ice_shape_meta)
ice.transformations = [Composition(Log10(), PiecewiseLinear(ice_n0_a_priori)),
                       Identity()]
ice.limits_low = [4, 1e-8]
ice.psd.cutoff_low = [1e2, 1e-8]

################################################################################
# Snow particles
################################################################################

snow_shape      = os.path.join(scattering_data, "8-ColumnAggregate.xml")
snow_shape_meta = os.path.join(scattering_data, "8-ColumnAggregate.meta.xml")
snow_mask       = And(AltitudeMask(0.0, 19e3), TemperatureMask(0.0, 276.0))

snow_covariance  = Diagonal(100e-6 ** 2, mask = snow_mask, mask_value = 1e-12)
snow_covariance  = SpatialCorrelation(snow_covariance, 2e3, mask = snow_mask)
snow_dm_a_priori = FixedAPriori("snow_n0", 1e-3, snow_covariance, mask = snow_mask, mask_value = 1e-12)
snow_dm_a_priori = ReferenceAPriori("snow_dm", snow_covariance, mask = snow_mask, mask_value = 1e-12,
                                    a_priori = snow_dm_a_priori,
                                    transformation = Identity())

snow_covariance  = Diagonal(0.25, mask = snow_mask, mask_value = 1e-12)
snow_covariance  = SpatialCorrelation(snow_covariance, 4e3, mask = snow_mask)
snow_n0_a_priori = FixedAPriori("snow_n0", 5, snow_covariance, mask = snow_mask, mask_value = 2)
snow_n0_a_priori = ReferenceAPriori("snow_n0", snow_covariance, mask = snow_mask, mask_value = 2,
                                    a_priori = snow_n0_a_priori,
                                    transformation = Log10())
snow_n0_a_priori = MaskedRegularGrid(snow_n0_a_priori, 5, ice_mask, "altitude", provide_retrieval_grid = False)

snow = Hydrometeor("snow", D14NDmIce(), [snow_n0_a_priori, snow_dm_a_priori], snow_shape, snow_shape_meta)
snow.transformations = [Composition(Log10(), PiecewiseLinear(snow_n0_a_priori)),
                       Identity()]
snow.limits_low = [2, 1e-8]
snow.psd.cutoff_low = [1e2, 1e-8]

################################################################################
# Rain particles
################################################################################

rain_shape      = os.path.join(scattering_data, "LiquidSphere.xml")
rain_shape_meta = os.path.join(scattering_data, "LiquidSphere.meta.xml")

rain_mask  = TemperatureMask(273, 340.0)
rain_covariance = Diagonal(500e-6 ** 2, mask = rain_mask, mask_value = 1e-12)
rain_dm_a_priori = FixedAPriori("rain_dm", 500e-6, rain_covariance, mask = rain_mask, mask_value = 1e-8)
rain_dm_a_priori = ReferenceAPriori("rain_dm", rain_covariance, mask = rain_mask, mask_value = 1e-8,
                                    a_priori = rain_dm_a_priori,
                                    transformation = Identity())
rain_dm_a_priori = MaskedRegularGrid(rain_dm_a_priori, 10, rain_mask, "altitude", provide_retrieval_grid = False)

z_grid = np.linspace(0, 12e3, 7)
rain_covariance = Diagonal(1, mask = rain_mask, mask_value = 1e-12)
rain_n0_a_priori = FixedAPriori("rain_n0", 7, rain_covariance, mask = rain_mask, mask_value = 2)
rain_n0_a_priori = ReferenceAPriori("rain_n0", rain_covariance, mask = rain_mask, mask_value = 2,
                                    a_priori = rain_n0_a_priori,
                                    transformation = Log10())
rain_n0_a_priori = MaskedRegularGrid(rain_n0_a_priori, 4, rain_mask, "altitude", provide_retrieval_grid = False)

rain = Hydrometeor("rain", D14NDmLiquid(), [rain_n0_a_priori, rain_dm_a_priori], rain_shape, rain_shape_meta)
rain.transformations = [Composition(Log10(), PiecewiseLinear(rain_n0_a_priori)),
                        Composition(Identity(), PiecewiseLinear(rain_dm_a_priori))]
rain.limits_low = [4, 1e-8]
rain.psd.cutoff_low = [1e2, 1e-8]

################################################################################
# Cloud liquid
################################################################################

liquid_mask = TemperatureMask(230, 273.0)
liquid_covariance = Diagonal(1 ** 2)
cloud_water_a_priori = FixedAPriori("cloud_water", -6, liquid_covariance,
                                    mask = liquid_mask, mask_value = -20)
cloud_water_a_priori = ReferenceAPriori("cloud_water", liquid_covariance,
                                        mask = liquid_mask, mask_value = -20,
                                        a_priori = cloud_water_a_priori,
                                        transformation = Log10())
cloud_water_a_priori = MaskedRegularGrid(cloud_water_a_priori, 7, liquid_mask,
                                         "altitude", provide_retrieval_grid = False)

################################################################################
# Humidity
################################################################################

def a_priori_shape(t):
    transformation = Atanh()
    transformation.z_max = 1.2
    transformation.z_min = 0.0
    x = np.maximum(np.minimum(0.7 - (270 - t) / 100.0, 0.7), 0.2)
    x = 0.5 * np.ones(t.shape)
    return transformation(x)

z_grid = np.linspace(0, 20e3, 21)
rh_covariance = Diagonal(1.0)
rh_covariance = SpatialCorrelation(rh_covariance, 2e3)
h2o_a_priori = FunctionalAPriori("H2O", "temperature", a_priori_shape, rh_covariance)
h2o_a_priori = ReferenceAPriori("H2O", rh_covariance, transformation = Atanh(0.0, 1.2),
                               a_priori = h2o_a_priori,
                               variable = "relative_humidity")
h2o_a_priori = ReducedVerticalGrid(h2o_a_priori, z_grid, "altitude",
                                  provide_retrieval_grid = False)
