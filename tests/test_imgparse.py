import os
from datetime import datetime, timedelta

import pytest
import pytz

import imgparse
from imgparse import ParsingError

base_path = os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def bad_data():
    return os.path.join(base_path, "bad_data", "BAD_IMG.jpg")


@pytest.fixture
def sentera_image_data():
    return os.path.join(base_path, "data", "IMG_00037.jpg")


@pytest.fixture
def dji_image_data():
    return os.path.join(base_path, "data", "DJI_0012.JPG")


@pytest.fixture
def sentera_6x_image_data():
    return os.path.join(base_path, "data", "IMG_0001_475_30.tif")


def test_get_camera_params_invalid(bad_data):
    with pytest.raises(FileNotFoundError):
        imgparse.get_camera_params(bad_data)


def test_get_camera_params_dji(dji_image_data):
    focal1, pitch1 = imgparse.get_camera_params(dji_image_data)
    focal2, pitch2 = imgparse.get_camera_params(
        dji_image_data, use_calibrated=True
    )

    assert [focal1, pitch1] == [0.0088, 2.41e-06]
    assert [focal2, pitch2] == pytest.approx([3.666666, 2.41e-06], abs=1e-06)


def test_get_camera_params_sentera(sentera_image_data):
    focal1, pitch1 = imgparse.get_camera_params(sentera_image_data)

    assert [focal1, pitch1] == pytest.approx([0.025, 1.55e-06], abs=1e-06)


def test_get_make_and_model_dji(dji_image_data):
    make1, model1 = imgparse.get_make_and_model(dji_image_data)

    assert [make1, model1] == ["DJI", "FC6310"]


def test_get_make_and_model_sentera(sentera_image_data):
    make1, model1 = imgparse.get_make_and_model(sentera_image_data)

    assert [make1, model1] == ["Sentera", "21022-06_12MP-ERS-0001"]


def test_get_relative_altitude_sentera(sentera_image_data):
    alt1 = imgparse.get_relative_altitude(sentera_image_data)
    alt3 = imgparse.get_relative_altitude(sentera_image_data, alt_source="lrf")

    sentera_image_path = os.path.join(base_path, "data", "IMG_00003.jpg")
    alt4 = imgparse.get_relative_altitude(sentera_image_path)
    alt5 = imgparse.get_relative_altitude(sentera_image_path, alt_source="lrf")

    assert alt1 == 51.042
    assert alt3 == 52.041  # AltimeterCalculatedAGL
    assert alt4 == pytest.approx(41.55, abs=1e-03)
    assert alt5 == 42.46  # AltimeterCalcuatedAGL


def test_get_relative_altitude_dji(dji_image_data):
    alt1 = imgparse.get_relative_altitude(dji_image_data)

    assert alt1 == 15.2


def test_get_altitude_msl_sentera(sentera_image_data):
    alt1 = imgparse.get_altitude_msl(sentera_image_data)

    assert alt1 == 50.592


def test_get_altitude_msl_dji(dji_image_data):
    alt1 = imgparse.get_altitude_msl(dji_image_data)

    assert alt1 == 282.401


def test_get_gsd_sentera(sentera_image_data):
    gsd1 = imgparse.get_gsd(sentera_image_data)

    assert gsd1 == pytest.approx(0.00316, rel=0.01)


def test_get_gsd_dji(dji_image_data):
    gsd1 = imgparse.get_gsd(dji_image_data)

    assert gsd1 == pytest.approx(0.00416, rel=0.01)


def test_get_lat_lon_sentera(sentera_image_data):
    lat1, lon1 = imgparse.get_lat_lon(sentera_image_data)

    assert [lat1, lon1] == pytest.approx([27.564768, -97.657411], abs=1e-06)


def test_get_lat_lon_dji(dji_image_data):
    lat1, lon1 = imgparse.get_lat_lon(dji_image_data)

    assert [lat1, lon1] == pytest.approx([45.514942, -93.973210], abs=1e-06)


def test_get_roll_pitch_yaw_sentera(sentera_image_data):
    roll1, pitch1, yaw1 = imgparse.get_roll_pitch_yaw(sentera_image_data)

    assert [roll1, pitch1, yaw1] == pytest.approx(
        [-2.445596, 1.003452, 29.639198], abs=1e-06
    )


def test_get_roll_pitch_yaw_dji(dji_image_data):
    roll1, pitch1, yaw1 = imgparse.get_roll_pitch_yaw(image_path=dji_image_data)

    assert [roll1, pitch1, yaw1] == pytest.approx([0, 0.1, 90.2], abs=1e-06)


def test_get_dimensions_sentera(sentera_image_data):
    height1, width1 = imgparse.get_dimensions(sentera_image_data)

    assert [height1, width1] == [3000, 4000]


def test_get_dimensions_6x(sentera_6x_image_data):
    height1, width1 = imgparse.get_dimensions(sentera_6x_image_data)

    assert [height1, width1] == [1464, 1952]


def test_get_dimensions_dji(dji_image_data):
    height1, width1 = imgparse.get_dimensions(dji_image_data)

    assert [height1, width1] == [3648, 4864]


def test_get_autoexposure_sentera(sentera_image_data):
    autoexposure1 = imgparse.get_autoexposure(sentera_image_data)

    assert autoexposure1 == pytest.approx(0.4105, rel=0.001)


def test_get_autoexposure_dji(dji_image_data):
    autoexposure1 = imgparse.get_autoexposure(dji_image_data)

    assert autoexposure1 == pytest.approx(0.0800, rel=0.001)


def test_get_timestamp_sentera(sentera_image_data):
    timestamp1 = imgparse.get_timestamp(sentera_image_data)

    correct_timestamp = datetime.strptime("2019:03:02 22:44:46", "%Y:%m:%d %H:%M:%S")
    correct_timestamp = pytz.utc.localize(correct_timestamp)

    assert abs(timestamp1 - correct_timestamp) < timedelta(seconds=1)


def test_get_timestamp_dji(dji_image_data):
    timestamp1 = imgparse.get_timestamp(dji_image_data)

    correct_timestamp = datetime.strptime("2018:05:22 17:03:27", "%Y:%m:%d %H:%M:%S")
    correct_timestamp = pytz.utc.localize(correct_timestamp)

    assert abs(timestamp1 - correct_timestamp) < timedelta(seconds=1)


def test_get_version_dji(dji_image_data):
    version1 = imgparse.get_firmware_version(dji_image_data)

    assert version1 == (1, 7, 1641)


def test_get_version_sentera(sentera_image_data):
    version1 = imgparse.get_firmware_version(sentera_image_data)

    assert version1 == (0, 22, 3)
