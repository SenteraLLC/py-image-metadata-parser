import os
from copy import deepcopy
from datetime import datetime, timedelta

import pytest
import pytz

import imgparse
from imgparse import ParsingError, TerrainAPIError

base_path = os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def bad_data():
    bad_path = os.path.join(base_path, "bad_data", "BAD_IMG.jpg")
    bad_dict = {"BadKey1": "BadValue1", "BadKey2": 0}
    bad_xmp = {"Bad Key1": "Bad Value1"}
    return [bad_path, bad_dict, bad_xmp]


@pytest.fixture
def sentera_image_data():
    sentera_image_path = os.path.join(base_path, "data", "sentera_normal.jpg")
    sentera_exif_data = imgparse.get_exif_data(sentera_image_path)
    sentera_xmp_data = imgparse.get_xmp_data(sentera_image_path)
    return [sentera_image_path, sentera_exif_data, sentera_xmp_data]


@pytest.fixture
def dji_image_data():
    dji_image_path = os.path.join(base_path, "data", "DJI_normal.JPG")
    dji_exif_data = imgparse.get_exif_data(dji_image_path)
    dji_xmp_data = imgparse.get_xmp_data(dji_image_path)
    return [dji_image_path, dji_exif_data, dji_xmp_data]


@pytest.fixture
def dji_homepoint_image_data():
    dji_image_path = os.path.join(base_path, "data", "DJI_home_point.jpg")
    dji_exif_data = imgparse.get_exif_data(dji_image_path)
    dji_xmp_data = imgparse.get_xmp_data(dji_image_path)
    return [dji_image_path, dji_exif_data, dji_xmp_data]


@pytest.fixture
def dji_ms_image_data():
    dji_ms_image_path = os.path.join(base_path, "data", "DJI_ms.tif")
    dji_ms_exif_data = imgparse.get_exif_data(dji_ms_image_path)
    dji_ms_xmp_data = imgparse.get_xmp_data(dji_ms_image_path)
    return [dji_ms_image_path, dji_ms_exif_data, dji_ms_xmp_data]


@pytest.fixture
def micasense_ms_image_data():
    micasense_ms_image_path = os.path.join(base_path, "data", "MicaSense_ms.tif")
    micasense_ms_exif_data = imgparse.get_exif_data(micasense_ms_image_path)
    micasense_ms_xmp_data = imgparse.get_xmp_data(micasense_ms_image_path)
    return [micasense_ms_image_path, micasense_ms_exif_data, micasense_ms_xmp_data]


@pytest.fixture
def parrot_ms_image_data():
    parrot_ms_image_path = os.path.join(base_path, "data", "Parrot_ms.TIF")
    parrot_ms_exif_data = imgparse.get_exif_data(parrot_ms_image_path)
    parrot_ms_xmp_data = imgparse.get_xmp_data(parrot_ms_image_path)
    return [parrot_ms_image_path, parrot_ms_exif_data, parrot_ms_xmp_data]


@pytest.fixture
def sentera_homepoint_image_data():
    image_path = os.path.join(base_path, "data", "IMG_00001.jpg")
    exif_data = imgparse.get_exif_data(image_path)
    xmp_data = imgparse.get_xmp_data(image_path)
    return [image_path, exif_data, xmp_data]


@pytest.fixture
def sentera_6x_image_data():
    sentera_6x_image_path = os.path.join(base_path, "data", "sentera_6x.tif")
    sentera_6x_exif_data = imgparse.get_exif_data(sentera_6x_image_path)
    sentera_6x_xmp_data = imgparse.get_xmp_data(sentera_6x_image_path)
    return [sentera_6x_image_path, sentera_6x_exif_data, sentera_6x_xmp_data]


@pytest.fixture
def sentera_6x_rgb_image_data():
    sentera_6x_rgb_image_path = os.path.join(base_path, "data", "sentera_6x_rgb.jpg")
    sentera_6x_rgb_exif_data = imgparse.get_exif_data(sentera_6x_rgb_image_path)
    sentera_6x_rgb_xmp_data = imgparse.get_xmp_data(sentera_6x_rgb_image_path)
    return [
        sentera_6x_rgb_image_path,
        sentera_6x_rgb_exif_data,
        sentera_6x_rgb_xmp_data,
    ]


@pytest.fixture
def sentera_quad_image_data():
    sentera_quad_image_path = os.path.join(base_path, "data", "sentera_quad.jpg")
    sentera_quad_exif_data = imgparse.get_exif_data(sentera_quad_image_path)
    sentera_quad_xmp_data = imgparse.get_xmp_data(sentera_quad_image_path)
    return [sentera_quad_image_path, sentera_quad_exif_data, sentera_quad_xmp_data]


@pytest.fixture
def sentera_65r_image_data():
    sentera_65r_image_path = os.path.join(base_path, "data", "sentera_65r.jpg")
    sentera_65r_exif_data = imgparse.get_exif_data(sentera_65r_image_path)
    sentera_65r_xmp_data = imgparse.get_xmp_data(sentera_65r_image_path)
    return [sentera_65r_image_path, sentera_65r_exif_data, sentera_65r_xmp_data]


def test_get_camera_params_invalid(bad_data):
    with pytest.raises(FileNotFoundError):
        imgparse.get_camera_params(bad_data[0])

    with pytest.raises(FileNotFoundError):
        imgparse.get_camera_params(bad_data[0], exif_data=bad_data[1])

    with pytest.raises(FileNotFoundError):
        imgparse.get_camera_params(bad_data[0], xmp_data=bad_data[2])

    with pytest.raises(ParsingError):
        imgparse.get_camera_params(
            bad_data[0], exif_data=bad_data[1], xmp_data=bad_data[2]
        )


def test_get_camera_params_dji(dji_image_data):
    focal1, pitch1 = imgparse.get_camera_params(dji_image_data[0])
    focal2, pitch2 = imgparse.get_camera_params(
        dji_image_data[0], use_calibrated_focal_length=True
    )
    assert [focal1, pitch1] == [0.0088, 2.41e-06]
    assert [focal2, pitch2] == pytest.approx([3.666666, 2.41e-06], abs=1e-06)


def test_get_camera_params_sentera(sentera_image_data):
    focal, pitch = imgparse.get_camera_params(sentera_image_data[0])
    focal2, pitch2 = imgparse.get_camera_params(
        sentera_image_data[0], use_calibrated_focal_length=True
    )

    assert [focal, pitch] == pytest.approx([0.025, 1.55e-06], abs=1e-06)
    assert [focal2, pitch2] == pytest.approx([0.025, 1.55e-06], abs=1e-06)


def test_get_make_and_model_invalid(bad_data):
    with pytest.raises(ParsingError):
        imgparse.get_camera_params(
            bad_data[0], exif_data=bad_data[1], xmp_data=bad_data[2]
        )


def test_get_make_and_model_dji(dji_image_data):
    make, model = imgparse.get_make_and_model(dji_image_data[0])
    assert [make, model] == ["DJI", "FC6310"]


def test_get_make_and_model_sentera(sentera_image_data):
    make, model = imgparse.get_make_and_model(sentera_image_data[0])
    assert [make, model] == ["Sentera", "21022-06_12MP-ERS-0001"]


def test_get_lens_model_invalid(dji_image_data):
    with pytest.raises(ParsingError):
        imgparse.get_lens_model(dji_image_data[0])


def test_get_lens_model_sentera(
    sentera_image_data, sentera_6x_image_data, sentera_65r_image_data
):
    lens_model1 = imgparse.get_lens_model(sentera_image_data[0])
    lens_model2 = imgparse.get_lens_model(sentera_6x_image_data[0])
    lens_model3 = imgparse.get_lens_model(sentera_65r_image_data[0])
    assert lens_model1 == "25.0mm-0001_0008"
    assert lens_model2 == "8.00mm-0005_0020"
    assert lens_model3 == "43.0mm-0001_0031"


def test_parse_session_alt_invalid(bad_data):
    with pytest.raises(ParsingError):
        imgparse.parse_session_alt(bad_data[0])


def test_parse_session_alt(sentera_image_data):
    alt = imgparse.parse_session_alt(sentera_image_data[0])
    assert alt == -0.4500


def test_get_relative_altitude_invalid(bad_data, dji_image_data):
    with pytest.raises(ParsingError):
        imgparse.get_relative_altitude(
            bad_data[0], exif_data=bad_data[1], xmp_data=bad_data[2]
        )

    with pytest.raises(ParsingError):
        imgparse.get_relative_altitude(
            dji_image_data[0], exif_data=dji_image_data[1], xmp_data=bad_data[2]
        )

    with pytest.raises(ParsingError):
        imgparse.get_relative_altitude(
            dji_image_data[0], exif_data=bad_data[1], xmp_data=dji_image_data[2]
        )


def test_get_relative_altitude_sentera(sentera_image_data, sentera_quad_image_data):
    alt1 = imgparse.get_relative_altitude(sentera_image_data[0])
    alt2 = imgparse.get_relative_altitude(sentera_image_data[0], alt_source="lrf")

    alt3 = imgparse.get_relative_altitude(sentera_quad_image_data[0])
    alt4 = imgparse.get_relative_altitude(sentera_quad_image_data[0], alt_source="lrf")

    assert alt1 == 51.042
    assert alt2 == 52.041  # AltimeterCalculatedAGL
    assert alt3 == pytest.approx(41.55, abs=1e-03)
    assert alt4 == 42.46  # AltimeterCalcuatedAGL


def test_get_relative_altitude_dji(dji_image_data):
    alt1 = imgparse.get_relative_altitude(dji_image_data[0])
    alt2 = imgparse.get_relative_altitude(dji_image_data[0], alt_source="lrf")
    assert alt1 == 15.2
    assert alt2 == 15.2


def test_get_altitude_msl_invalid(bad_data):
    with pytest.raises(ParsingError):
        imgparse.get_altitude_msl(bad_data[0], exif_data=bad_data[1])


def test_get_altitude_msl_sentera(sentera_image_data):
    alt = imgparse.get_altitude_msl(sentera_image_data[0])
    assert alt == 50.592


def test_get_altitude_msl_dji(dji_image_data):
    alt = imgparse.get_altitude_msl(dji_image_data[0])
    assert alt == 282.401


def test_get_gsd_invalid(bad_data):
    with pytest.raises(ParsingError):
        imgparse.get_gsd(bad_data[0], exif_data=bad_data[1], xmp_data=bad_data[2])


def test_get_gsd_sentera(sentera_image_data):
    gsd = imgparse.get_gsd(sentera_image_data[0])
    assert gsd == pytest.approx(0.00316, rel=0.01)


def test_get_gsd_dji(dji_image_data):
    gsd = imgparse.get_gsd(dji_image_data[0])
    assert gsd == pytest.approx(0.00416, rel=0.01)


def test_get_lat_lon_invalid(bad_data):
    with pytest.raises(ParsingError):
        imgparse.get_lat_lon(bad_data[0], exif_data=bad_data[1])


def test_get_lat_lon_sentera(sentera_image_data):
    lat, lon = imgparse.get_lat_lon(sentera_image_data[0])
    assert [lat, lon] == pytest.approx([27.564768, -97.657411], abs=1e-06)


def test_get_lat_lon_dji(dji_image_data):
    lat, lon = imgparse.get_lat_lon(dji_image_data[0])
    assert [lat, lon] == pytest.approx([45.514942, -93.973210], abs=1e-06)


def test_get_roll_pitch_yaw_invalid(bad_data, dji_image_data):
    with pytest.raises(ParsingError):
        imgparse.get_roll_pitch_yaw(
            bad_data[0], exif_data=bad_data[1], xmp_data=bad_data[2]
        )

    exif_data = deepcopy(dji_image_data[1])
    exif_data["Image Make"].values = "Bad Make"
    with pytest.raises(ParsingError):
        imgparse.get_roll_pitch_yaw(
            dji_image_data[0], exif_data=exif_data, xmp_data=dji_image_data[2]
        )


def test_get_roll_pitch_yaw_sentera(sentera_image_data):
    roll, pitch, yaw = imgparse.get_roll_pitch_yaw(sentera_image_data[0])
    assert [roll, pitch, yaw] == pytest.approx(
        [-2.445596, 1.003452, 29.639198], abs=1e-06
    )


def test_get_roll_pitch_yaw_dji(dji_image_data):
    roll, pitch, yaw = imgparse.get_roll_pitch_yaw(dji_image_data[0])
    assert [roll, pitch, yaw] == pytest.approx([0, 0.1, 90.2], abs=1e-06)


def test_get_dimensions_invalid(bad_data):
    with pytest.raises(ParsingError):
        imgparse.get_dimensions(bad_data[0], exif_data=bad_data[1])

    with pytest.raises(ParsingError):
        imgparse.get_dimensions("/bad/path.png", exif_data=bad_data[1])


def test_get_dimensions_sentera(sentera_image_data):
    height, width = imgparse.get_dimensions(sentera_image_data[0])
    assert [height, width] == [3000, 4000]


def test_get_dimensions_6x(sentera_6x_image_data):
    height, width = imgparse.get_dimensions(sentera_6x_image_data[0])
    assert [height, width] == [1464, 1952]


def test_get_dimensions_6x_rgb(sentera_6x_rgb_image_data):
    height, width = imgparse.get_dimensions(sentera_6x_rgb_image_data[0])
    assert [height, width] == [3888, 5184]


def test_get_dimensions_65r(sentera_65r_image_data):
    height, width = imgparse.get_dimensions(sentera_65r_image_data[0])
    assert [height, width] == [7000, 9344]


def test_get_dimensions_dji(dji_image_data):
    height, width = imgparse.get_dimensions(dji_image_data[0])
    assert [height, width] == [3648, 4864]


def test_get_principal_point_65r(sentera_65r_image_data):
    x, y = imgparse.get_principal_point(sentera_65r_image_data[0])
    assert [x, y] == [14.916, 11.14]


def test_get_distortion_params_65r(sentera_65r_image_data):
    params = imgparse.get_distortion_parameters(sentera_65r_image_data[0])
    assert params == [-0.127, 0.126, 0.097, 0.0, 0.0]


def test_get_autoexposure_sentera(sentera_image_data):
    autoexposure = imgparse.get_autoexposure(sentera_image_data[0])
    assert autoexposure == pytest.approx(0.4105, rel=0.001)


def test_get_autoexposure_dji(dji_image_data):
    autoexposure = imgparse.get_autoexposure(dji_image_data[0])
    assert autoexposure == pytest.approx(0.0800, rel=0.001)


def test_get_timestamp_sentera(sentera_image_data):
    timestamp = imgparse.get_timestamp(sentera_image_data[0])

    correct_timestamp = datetime.strptime("2019:03:02 22:44:46", "%Y:%m:%d %H:%M:%S")
    correct_timestamp = pytz.utc.localize(correct_timestamp)

    assert abs(timestamp - correct_timestamp) < timedelta(seconds=1)


def test_get_timestamp_dji(dji_image_data):
    timestamp = imgparse.get_timestamp(dji_image_data[0])

    correct_timestamp = datetime.strptime("2018:05:22 17:03:27", "%Y:%m:%d %H:%M:%S")
    correct_timestamp = pytz.utc.localize(correct_timestamp)

    assert abs(timestamp - correct_timestamp) < timedelta(seconds=1)


def test_get_ils_6x(sentera_6x_image_data):
    ils = imgparse.get_ils(sentera_6x_image_data[0])
    assert ils == [10532.165]


def test_get_ils_non6x(dji_image_data):
    with pytest.raises(ParsingError):
        imgparse.get_ils(dji_image_data[0])

    with pytest.raises(ParsingError):
        imgparse.get_ils(dji_image_data[0], xmp_data=dji_image_data[2])


def test_get_version_dji(dji_image_data):
    version = imgparse.get_firmware_version(dji_image_data[0])
    assert version == (1, 7, 1641)


def test_get_version_sentera(sentera_image_data):
    version = imgparse.get_firmware_version(sentera_image_data[0])
    assert version == (0, 22, 3)


def test_bad_version(dji_image_data):
    exif_data = deepcopy(dji_image_data[1])
    exif_data["Image Software"].values = "Bad Version"
    with pytest.raises(ParsingError):
        imgparse.get_firmware_version(dji_image_data[0], exif_data=exif_data)


def test_bad_autoexposure(dji_image_data):
    exif_data = deepcopy(dji_image_data[1])
    exif_data.pop("EXIF ISOSpeedRatings")
    with pytest.raises(ParsingError):
        imgparse.get_autoexposure(dji_image_data[0], exif_data=exif_data)


def test_bad_timestamp(dji_image_data):
    exif_data = deepcopy(dji_image_data[1])
    exif_data["EXIF DateTimeOriginal"].values = "Bad Timestamp"
    with pytest.raises(ParsingError):
        imgparse.get_timestamp(dji_image_data[0], exif_data=exif_data)

    exif_data.pop("EXIF DateTimeOriginal")
    with pytest.raises(ParsingError):
        imgparse.get_timestamp(dji_image_data[0], exif_data=exif_data)


def test_bad_pixel_pitch(dji_image_data):
    exif_data = deepcopy(dji_image_data[1])
    exif_data["Image Model"].values = "Bad Model"
    with pytest.raises(ParsingError):
        imgparse.get_pixel_pitch(dji_image_data[0], exif_data=exif_data)


def test_invalid_bandnames(dji_image_data):
    with pytest.raises(ParsingError):
        imgparse.get_bandnames(dji_image_data[0])


def test_invalid_wavelength_data(dji_image_data):
    with pytest.raises(ParsingError):
        imgparse.get_wavelength_data(dji_image_data[0])


def test_get_bandnames(
    sentera_6x_image_data,
    sentera_quad_image_data,
    dji_ms_image_data,
    micasense_ms_image_data,
    parrot_ms_image_data,
):
    bandnames1 = imgparse.get_bandnames(sentera_6x_image_data[0])
    bandnames2 = imgparse.get_bandnames(sentera_quad_image_data[0])
    bandnames3 = imgparse.get_bandnames(dji_ms_image_data[0])
    bandnames4 = imgparse.get_bandnames(micasense_ms_image_data[0])
    bandnames5 = imgparse.get_bandnames(parrot_ms_image_data[0])

    assert bandnames1 == ["Blue"]
    assert bandnames2 == ["Red", "Green", "Blue"]
    assert bandnames3 == ["Blue"]
    assert bandnames4 == ["Blue"]
    assert bandnames5 == ["Green"]


def test_get_wavelength_data(
    sentera_6x_image_data,
    sentera_quad_image_data,
    dji_ms_image_data,
    micasense_ms_image_data,
    parrot_ms_image_data,
):
    central1, fwhm1 = imgparse.get_wavelength_data(sentera_6x_image_data[0])
    central2, fwhm2 = imgparse.get_wavelength_data(sentera_quad_image_data[0])
    central3, fwhm3 = imgparse.get_wavelength_data(dji_ms_image_data[0])
    central4, fwhm4 = imgparse.get_wavelength_data(micasense_ms_image_data[0])
    central5, fwhm5 = imgparse.get_wavelength_data(parrot_ms_image_data[0])

    assert central1 == [475]
    assert fwhm1 == [30]
    assert central2 == [630, 525, 450]
    assert fwhm2 == [125, 160, 130]
    assert central3 == [450]
    assert fwhm3 == [16]
    assert central4 == [475]
    assert fwhm4 == [32]
    assert central5 == [550]
    assert fwhm5 == [40]


def test_dji_terrain_elevation(dji_homepoint_image_data, requests_mock):
    mock = requests_mock.get(
        imgparse.imgparse.TERRAIN_URL,
        [
            {"json": {"status": "OK", "results": [{"elevation": 50}]}},
            {"json": {"status": "OK", "results": [{"elevation": 0}]}},
        ],
    )
    alt = imgparse.get_relative_altitude(
        dji_homepoint_image_data[0], alt_source="terrain"
    )
    assert alt == 171.4

    alt = imgparse.get_relative_altitude(
        dji_homepoint_image_data[0], alt_source="terrain"
    )
    assert alt == 171.4
    # Make sure home point only requested once
    assert len(mock.request_history) == 3

    requests_mock.get(imgparse.imgparse.TERRAIN_URL, json={"status": "ERROR"})
    alt2 = imgparse.get_relative_altitude(
        dji_homepoint_image_data[0], alt_source="terrain"
    )
    assert alt2 == 121.4

    with pytest.raises(TerrainAPIError):
        imgparse.get_relative_altitude(
            dji_homepoint_image_data[0], alt_source="terrain", fallback=False
        )


def test_sentera_terrain_elevation(sentera_homepoint_image_data, requests_mock):
    mock = requests_mock.get(
        imgparse.imgparse.TERRAIN_URL,
        [
            {"json": {"status": "OK", "results": [{"elevation": 50}]}},
            {"json": {"status": "OK", "results": [{"elevation": 0}]}},
        ],
    )
    alt = imgparse.get_relative_altitude(
        sentera_homepoint_image_data[0], alt_source="terrain"
    )
    assert alt == pytest.approx(114.45, 0.01)

    alt = imgparse.get_relative_altitude(
        sentera_homepoint_image_data[0], alt_source="terrain"
    )
    assert alt == pytest.approx(114.45, 0.01)

    alt = imgparse.get_relative_altitude(
        sentera_homepoint_image_data[0], alt_source="terrain", fallback=False
    )
    assert alt == pytest.approx(114.45, 0.01)

    # Make sure home point only requested once
    assert len(mock.request_history) == 4

    requests_mock.get(imgparse.imgparse.TERRAIN_URL, json={"status": "ERROR"})
    alt2 = imgparse.get_relative_altitude(
        sentera_homepoint_image_data[0], alt_source="terrain"
    )
    assert alt2 == pytest.approx(64.45, 0.01)

    with pytest.raises(TerrainAPIError):
        imgparse.get_relative_altitude(
            sentera_homepoint_image_data[0], alt_source="terrain", fallback=False
        )


def test_get_homepoint_invalid(sentera_image_data):
    with pytest.raises(ParsingError):
        imgparse.get_home_point(sentera_image_data[0])
