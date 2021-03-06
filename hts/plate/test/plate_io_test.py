import os
import logging

import pytest

from hts.plate_data import readout_io

logging.basicConfig(level=logging.INFO)

# Test file names
TEST_FILE_LUMINESCENCE_CSV = 'dPIA_example_Bei.csv'
TEST_FILE_FRET_CSV = '164110_13383_p4mo3000.csv'
TEST_FOLDER_LUMINESCENCE_CSV = "luminescence_cell_viability_QC"
TEST_FOLDER_LUMINESCENCE_CSV_FIRST_FILE_PARAMTERS = {'Ambient temperature at end': 'N/A', 'Humidity at end': 'N/A', 'Measured height': 'N/A', 'Formula': 'Calc 1: Crosstalk = Crosstalk correction where Label : US LUM 384 (cps)(1) channel 1', 'Chamber temperature at end': 'N/A', 'Measurement date': '5/23/2015 16:33:33', 'Plate': '1', 'Humidity at start': 'N/A', 'Repeat': '1', 'Chamber temperature at start': 'N/A', 'Barcode': '', 'Ambient temperature at start': 'N/A'}
TEST_FILE_FLUORESCENCE_CSV = "miRNA_fluorescence_test_1.csv"
TEST_FILE_SIRNA = "siRNA_12599.csv"
TEST_FILE_INSULIN_CSV = os.path.join("insulin", "test_1.csv")


notfixed = pytest.mark.notfixed

@pytest.fixture
def path():
    """Return the path to the test data files.
    """
    return os.path.join(os.path.abspath('.'), '../', 'test_data', 'Raw_data')

@pytest.fixture
def path_siRNA():
    """Return the path to the test data files.
    """
    return os.path.join(os.path.abspath('.'), '../', 'test_data', 'Raw_data', 'siRNA')

@pytest.mark.no_external_software_required
def test_envision_luminesence_csv_read(path):
    test_plate_info, test_channel_wise_reads, test_channel_wise_info = readout_io.read_envision_csv(os.path.join(path, TEST_FILE_LUMINESCENCE_CSV))
    assert len(test_channel_wise_reads) == 2


@pytest.mark.no_external_software_required
def test_envision_fret_csv_read(path):
    test_plate_info, test_channel_wise_reads, test_channel_wise_info = readout_io.read_envision_csv(os.path.join(path, TEST_FILE_FRET_CSV))
    assert len(test_channel_wise_reads) == 2


@pytest.mark.no_external_software_required
def test_envision_fluorescence_csv_read(path):
    test_plate_info, test_channel_wise_reads, test_channel_wise_info = readout_io.read_envision_csv(os.path.join(path, TEST_FILE_FLUORESCENCE_CSV))
    assert len(test_channel_wise_reads) == 3


@pytest.mark.no_external_software_required
def test_insulin_csv_read(path):
    test_plate_info, test_channel_wise_reads, test_channel_wise_info = readout_io.read_insulin_csv(os.path.join(path, TEST_FILE_INSULIN_CSV))
    assert len(test_channel_wise_reads) == 481
    for i_test_plate_element in test_channel_wise_reads.values():
        assert len(i_test_plate_element) == 16
        assert len(i_test_plate_element[0]) == 24


@pytest.mark.no_external_software_required
def test_siRNA_csv_read(path_siRNA):
    test_plate_info, test_channel_wise_reads, test_channel_wise_info = readout_io.read_envision_csv(os.path.join(path_siRNA, TEST_FILE_SIRNA))
    assert len(test_channel_wise_reads) == 2
    for i_test_plate_element in test_channel_wise_reads.values():
        assert len(i_test_plate_element) == 16
        assert len(i_test_plate_element[0]) == 24