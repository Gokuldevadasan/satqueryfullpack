import unittest
import numpy as np
from gis.band_registry import identify_bands, required_message
from gis.spectral_indices import ndvi, ndwi, ndbi

class GisBasics(unittest.TestCase):
    def test_b03_single_band_is_green(self):
        names, mapping, details=identify_bands('B03.tif', (), 1)
        self.assertEqual(names, ['B03']); self.assertEqual(mapping, {'B03': 0})
        self.assertEqual(details[0]['name'], 'Green')
        self.assertIn('B08 (NIR)', required_message('NDVI', mapping))
    def test_indices_and_zero_denominator(self):
        data=np.array([[[0,1]],[[2,3]],[[1,1]],[[3,0]],[[0,0]]],dtype=np.float32)
        bands={'green':1,'red':2,'nir':3,'swir':4}
        self.assertAlmostEqual(ndvi(data,bands)[0][0,0], .5)
        self.assertAlmostEqual(ndwi(data,bands)[0][0,0], -.2)
        self.assertAlmostEqual(ndbi(data,bands)[0][0,0], -1)
        self.assertTrue(np.isnan(ndbi(data,bands)[0][0,1]))
