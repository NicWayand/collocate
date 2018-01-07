"""
 Module to test the collocation routines
"""
import unittest
import datetime as dt

from nose.tools import eq_
import numpy as np

from colocate.kernels import moments
from colocate import collocate
from colocate.test import mock


class TestGeneralUngriddedCollocator(unittest.TestCase):

    def test_averaging_basic_col_in_4d(self):
        ug_data = mock.make_regular_4d_ungridded_data()
        # Note - This isn't actually used for averaging
        sample_points = mock.make_dummy_sample_points(lat=[1.0], lon=[1.0], alt=[12.0], time=[dt.datetime(1984, 8, 29, 8, 34)])

        new_data = collocate(sample_points, ug_data, moments())
        means = new_data[0]
        std_dev = new_data[1]
        no_points = new_data[2]

        eq_(means.name(), 'rainfall_flux')
        eq_(std_dev.name(), 'Corrected sample standard deviation of TOTAL RAINFALL RATE: LS+CONV KG/M2/S')
        eq_(no_points.name(), 'Number of points used to calculate the mean of TOTAL RAINFALL RATE: LS+CONV KG/M2/S')
        assert means.coords()
        assert std_dev.coords()
        assert no_points.coords()

    def test_ungridded_ungridded_box_moments(self):
        data = mock.make_regular_2d_ungridded_data()
        sample = mock.make_dummy_sample_points(lat=[1.0, 3.0, -1.0], lon=[1.0, 3.0, -1.0], alt=[12.0, 7.0, 5.0],
                                               time=[dt.datetime(1984, 8, 29, 8, 34),
                                                     dt.datetime(1984, 8, 29, 8, 34),
                                                     dt.datetime(1984, 8, 29, 8, 34)])

        kernel = moments()

        output = collocate(sample, data, kernel, h_sep='500km')

        expected_result = np.array([28.0/3, 10.0, 20.0/3])
        expected_stddev = np.array([1.52752523, 1.82574186, 1.52752523])
        expected_n = np.array([3, 4, 3])
        assert len(output) == 3
        assert isinstance(output, DataList)
        assert np.allclose(output[0].data, expected_result)
        assert np.allclose(output[1].data, expected_stddev)
        assert np.allclose(output[2].data, expected_n)

    def test_ungridded_ungridded_box_moments_missing_data_for_missing_sample(self):
        data = mock.make_regular_2d_ungridded_data()
        sample = mock.make_dummy_sample_points(lat=[1.0, 3.0, -1.0], lon=[1.0, 3.0, -1.0], alt=[12.0, 7.0, 5.0],
                                               time=[dt.datetime(1984, 8, 29, 8, 34),
                                                     dt.datetime(1984, 8, 29, 8, 34),
                                                     dt.datetime(1984, 8, 29, 8, 34)])

        kernel = moments()

        sample_mask = [False, True, False]
        sample.data = np.ma.array([0, 0, 0], mask=sample_mask)

        output = collocate(sample, data, kernel, h_sep='500km', missing_data_for_missing_sample=True)

        assert len(output) == 3
        assert isinstance(output, DataList)
        assert np.array_equal(output[0].data.mask, sample_mask)
        assert np.array_equal(output[1].data.mask, sample_mask)
        assert np.array_equal(output[2].data.mask, sample_mask)

    def test_ungridded_ungridded_box_moments_no_missing_data_for_missing_sample(self):
        data = mock.make_regular_2d_ungridded_data()
        sample = mock.make_dummy_sample_points(lat=[1.0, 3.0, -1.0], lon=[1.0, 3.0, -1.0], alt=[12.0, 7.0, 5.0],
                                               time=[dt.datetime(1984, 8, 29, 8, 34),
                                                     dt.datetime(1984, 8, 29, 8, 34),
                                                     dt.datetime(1984, 8, 29, 8, 34)])

        kernel = moments()

        sample_mask = [False, True, False]
        sample.data = np.ma.array([0, 0, 0], mask=sample_mask)

        output = collocate(sample, data, kernel, h_sep='500km', missing_data_for_missing_sample=False)

        assert len(output) == 3
        assert isinstance(output, DataList)
        assert not any(output[0].data.mask)
        assert not any(output[1].data.mask)
        assert not any(output[2].data.mask)

    def test_list_ungridded_ungridded_box_mean(self):
        ug_data_1 = mock.make_regular_2d_ungridded_data()
        ug_data_2 = mock.make_regular_2d_ungridded_data(data_offset=3)
        ug_data_2.long_name = 'TOTAL SNOWFALL RATE: LS+CONV KG/M2/S'
        ug_data_2.standard_name = 'snowfall_flux'
        ug_data_2.var_name = 'snow'

        data_list = DataList([ug_data_1, ug_data_2])
        sample_points = mock.make_regular_2d_ungridded_data()
        kernel = moments()
        output = collocate(sample_points, data_list, kernel, h_sep='500km')

        expected_result = np.array(list(range(1, 16)))
        expected_n = np.array(15 * [1])
        assert len(output) == 6
        assert isinstance(output, DataList)
        assert output[3].var_name == 'snow'
        assert output[4].var_name == 'snow_std_dev'
        assert output[5].var_name == 'snow_num_points'
        assert np.allclose(output[0].data, expected_result)
        assert all(output[1].data.mask)
        assert np.allclose(output[2].data, expected_n)
        assert np.allclose(output[3].data, expected_result + 3)
        assert all(output[4].data.mask)
        assert np.allclose(output[5].data, expected_n)

if __name__ == '__main__':
    import nose
    nose.runmodule()
