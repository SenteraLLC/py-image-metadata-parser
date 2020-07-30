import os
from datetime import datetime, timedelta

import pytest

import imgparse
from imgparse import ParsingError

base_path = os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def bad_data():
    bad_path = os.path.join(base_path, "bad_data", "BAD_IMG.jpg")
    bad_dict = {"BadKey1": "BadValue1", "BadKey2": 0}
    bad_xmp = "Bad XMP string"
    return [bad_path, bad_dict, bad_xmp]


@pytest.fixture
def sentera_image_data():
    sentera_image_path = os.path.join(base_path, "data", "IMG_00037.jpg")
    sentera_exif_data = imgparse.get_exif_data(sentera_image_path)
    sentera_xmp_data = imgparse.get_xmp_data(sentera_image_path)
    return [sentera_image_path, sentera_exif_data, sentera_xmp_data]


@pytest.fixture
def dji_image_data():
    dji_image_path = os.path.join(base_path, "data", "DJI_0012.JPG")
    dji_exif_data = imgparse.get_exif_data(dji_image_path)
    dji_xmp_data = imgparse.get_xmp_data(dji_image_path)
    return [dji_image_path, dji_exif_data, dji_xmp_data]


@pytest.fixture
def sentera_6x_image_data():
    sentera_6x_image_path = os.path.join(base_path, "data", "IMG_0001_475_30.tif")
    sentera_6x_exif_data = imgparse.get_exif_data(sentera_6x_image_path)
    sentera_6x_xmp_data = imgparse.get_xmp_data(sentera_6x_image_path)
    return [sentera_6x_image_path, sentera_6x_exif_data, sentera_6x_xmp_data]


def test_get_camera_params_invalid(bad_data):
    with pytest.raises(ValueError):
        imgparse.get_camera_params()

    with pytest.raises(ValueError):
        imgparse.get_camera_params(bad_data[0])

    with pytest.raises(ParsingError):
        imgparse.get_camera_params(exif_data=bad_data[1])

    with pytest.raises(ParsingError):
        imgparse.get_camera_params(bad_data[0], exif_data=bad_data[1])


def test_get_camera_params_dji(dji_image_data):
    focal1, pitch1 = imgparse.get_camera_params(dji_image_data[0])
    focal2, pitch2 = imgparse.get_camera_params(exif_data=dji_image_data[1])
    focal3, pitch3 = imgparse.get_camera_params(
        dji_image_data[0], exif_data=dji_image_data[1]
    )

    assert [focal1, pitch1] == [0.0088, 2.41e-06]
    assert [focal2, pitch2] == [0.0088, 2.41e-06]
    assert [focal3, pitch3] == [0.0088, 2.41e-06]


def test_get_camera_params_sentera(sentera_image_data):
    focal1, pitch1 = imgparse.get_camera_params(sentera_image_data[0])
    focal2, pitch2 = imgparse.get_camera_params(exif_data=sentera_image_data[1])
    focal3, pitch3 = imgparse.get_camera_params(
        sentera_image_data[0], exif_data=sentera_image_data[1]
    )

    assert [focal1, pitch1] == pytest.approx([0.025, 1.55e-06], abs=1e-06)
    assert [focal2, pitch2] == pytest.approx([0.025, 1.55e-06], abs=1e-06)
    assert [focal3, pitch3] == pytest.approx([0.025, 1.55e-06], abs=1e-06)


def test_get_make_and_model_invalid(bad_data):
    with pytest.raises(ValueError):
        imgparse.get_camera_params()

    with pytest.raises(ValueError):
        imgparse.get_camera_params(bad_data[0])

    with pytest.raises(ParsingError):
        imgparse.get_camera_params(exif_data=bad_data[1])

    with pytest.raises(ParsingError):
        imgparse.get_camera_params(bad_data[0], exif_data=bad_data[1])


def test_get_make_and_model_dji(dji_image_data):
    make1, model1 = imgparse.get_make_and_model(dji_image_data[0])
    make2, model2 = imgparse.get_make_and_model(exif_data=dji_image_data[1])
    make3, model3 = imgparse.get_make_and_model(
        dji_image_data[0], exif_data=dji_image_data[1]
    )

    assert [make1, model1] == ["DJI", "FC6310"]
    assert [make2, model2] == ["DJI", "FC6310"]
    assert [make3, model3] == ["DJI", "FC6310"]


def test_get_make_and_model_sentera(sentera_image_data):
    make1, model1 = imgparse.get_make_and_model(sentera_image_data[0])
    make2, model2 = imgparse.get_make_and_model(exif_data=sentera_image_data[1])
    make3, model3 = imgparse.get_make_and_model(
        sentera_image_data[0], exif_data=sentera_image_data[1]
    )

    assert [make1, model1] == ["Sentera", "21022-06_12MP-ERS-0001"]
    assert [make2, model2] == ["Sentera", "21022-06_12MP-ERS-0001"]
    assert [make3, model3] == ["Sentera", "21022-06_12MP-ERS-0001"]


def test_parse_session_alt_invalid(bad_data):
    with pytest.raises(ParsingError):
        imgparse.parse_session_alt(bad_data[0])


def test_parse_session_alt(sentera_image_data):
    alt = imgparse.parse_session_alt(sentera_image_data[0])

    assert alt == -0.4500


def test_get_relative_altitude_invalid(bad_data, dji_image_data):
    with pytest.raises(ValueError):
        imgparse.get_relative_altitude(bad_data[0])

    with pytest.raises(ValueError):
        imgparse.get_relative_altitude(bad_data[0], exif_data=bad_data[1])

    with pytest.raises(ValueError):
        imgparse.get_relative_altitude(bad_data[0], xmp_data=bad_data[2])

    with pytest.raises(ParsingError):
        imgparse.get_relative_altitude(
            bad_data[0], exif_data=bad_data[1], xmp_data=bad_data[2]
        )

    with pytest.raises(ParsingError):
        imgparse.get_relative_altitude(
            dji_image_data[0], exif_data=dji_image_data[1], xmp_data="Bad xmp"
        )


def test_get_relative_altitude_sentera(sentera_image_data):
    alt1 = imgparse.get_relative_altitude(sentera_image_data[0])
    alt2 = imgparse.get_relative_altitude(
        sentera_image_data[0], exif_data=sentera_image_data[1]
    )

    sentera_image_path = os.path.join(base_path, "data", "IMG_00003.jpg")
    alt3 = imgparse.get_relative_altitude(sentera_image_path)

    assert alt1 == 51.042
    assert alt2 == 51.042
    assert alt3 == pytest.approx(41.55, abs=1e-03)


def test_get_relative_altitude_dji(dji_image_data):
    alt1 = imgparse.get_relative_altitude(dji_image_data[0])
    alt2 = imgparse.get_relative_altitude(
        dji_image_data[0], exif_data=dji_image_data[1]
    )

    assert alt1 == 15.2
    assert alt2 == 15.2


def test_get_altitude_msl_invalid(bad_data):
    with pytest.raises(ValueError):
        imgparse.get_altitude_msl()

    with pytest.raises(ValueError):
        imgparse.get_altitude_msl(bad_data[0])

    with pytest.raises(ParsingError):
        imgparse.get_altitude_msl(exif_data=bad_data[1])

    with pytest.raises(ParsingError):
        imgparse.get_altitude_msl(bad_data[0], exif_data=bad_data[1])


def test_get_altitude_msl_sentera(sentera_image_data):
    alt1 = imgparse.get_altitude_msl(sentera_image_data[0])
    alt2 = imgparse.get_altitude_msl(exif_data=sentera_image_data[1])
    alt3 = imgparse.get_altitude_msl(
        sentera_image_data[0], exif_data=sentera_image_data[1]
    )

    assert alt1 == 50.592
    assert alt2 == 50.592
    assert alt3 == 50.592


def test_get_altitude_msl_dji(dji_image_data):
    alt1 = imgparse.get_altitude_msl(dji_image_data[0])
    alt2 = imgparse.get_altitude_msl(exif_data=dji_image_data[1])
    alt3 = imgparse.get_altitude_msl(dji_image_data[0], exif_data=dji_image_data[1])

    assert alt1 == 282.401
    assert alt2 == 282.401
    assert alt3 == 282.401


def test_get_gsd_invalid(bad_data):
    with pytest.raises(ValueError):
        imgparse.get_gsd(bad_data[0])

    with pytest.raises(ParsingError):
        imgparse.get_gsd(bad_data[0], exif_data=bad_data[1])

    with pytest.raises(ValueError):
        imgparse.get_gsd(bad_data[0], xmp_data=bad_data[1])

    with pytest.raises(ParsingError):
        imgparse.get_gsd(bad_data[0], exif_data=bad_data[1], xmp_data=bad_data[2])


def test_get_gsd_sentera(sentera_image_data):
    gsd1 = imgparse.get_gsd(sentera_image_data[0])
    gsd2 = imgparse.get_gsd(sentera_image_data[0], exif_data=sentera_image_data[1])
    gsd3 = imgparse.get_gsd(sentera_image_data[0], xmp_data=sentera_image_data[2])
    gsd4 = imgparse.get_gsd(
        sentera_image_data[0],
        exif_data=sentera_image_data[1],
        xmp_data=sentera_image_data[2],
    )

    assert gsd1 == pytest.approx(0.00316, rel=0.01)
    assert gsd2 == pytest.approx(0.00316, rel=0.01)
    assert gsd3 == pytest.approx(0.00316, rel=0.01)
    assert gsd4 == pytest.approx(0.00316, rel=0.01)


def test_get_gsd_dji(dji_image_data):
    gsd1 = imgparse.get_gsd(dji_image_data[0])
    gsd2 = imgparse.get_gsd(dji_image_data[0], exif_data=dji_image_data[1])
    gsd3 = imgparse.get_gsd(dji_image_data[0], xmp_data=dji_image_data[2])
    gsd4 = imgparse.get_gsd(
        dji_image_data[0], exif_data=dji_image_data[1], xmp_data=dji_image_data[2]
    )

    assert gsd1 == pytest.approx(0.00416, rel=0.01)
    assert gsd2 == pytest.approx(0.00416, rel=0.01)
    assert gsd3 == pytest.approx(0.00416, rel=0.01)
    assert gsd4 == pytest.approx(0.00416, rel=0.01)


def test_get_lat_lon_invalid(bad_data):
    with pytest.raises(ValueError):
        imgparse.get_lat_lon()

    with pytest.raises(ValueError):
        imgparse.get_lat_lon(bad_data[0])

    with pytest.raises(ParsingError):
        imgparse.get_lat_lon(exif_data=bad_data[1])

    with pytest.raises(ParsingError):
        imgparse.get_lat_lon(bad_data[0], exif_data=bad_data[1])


def test_get_lat_lon_sentera(sentera_image_data):
    lat1, lon1 = imgparse.get_lat_lon(sentera_image_data[0])
    lat2, lon2 = imgparse.get_lat_lon(exif_data=sentera_image_data[1])
    lat3, lon3 = imgparse.get_lat_lon(
        sentera_image_data[0], exif_data=sentera_image_data[1]
    )

    assert [lat1, lon1] == pytest.approx([27.564768, -97.657411], abs=1e-06)
    assert [lat2, lon2] == pytest.approx([27.564768, -97.657411], abs=1e-06)
    assert [lat3, lon3] == pytest.approx([27.564768, -97.657411], abs=1e-06)


def test_get_lat_lon_dji(dji_image_data):
    lat1, lon1 = imgparse.get_lat_lon(dji_image_data[0])
    lat2, lon2 = imgparse.get_lat_lon(exif_data=dji_image_data[1])
    lat3, lon3 = imgparse.get_lat_lon(dji_image_data[0], exif_data=dji_image_data[1])

    assert [lat1, lon1] == pytest.approx([45.514942, -93.973210], abs=1e-06)
    assert [lat2, lon2] == pytest.approx([45.514942, -93.973210], abs=1e-06)
    assert [lat3, lon3] == pytest.approx([45.514942, -93.973210], abs=1e-06)


def test_get_roll_pitch_yaw_invalid(bad_data, dji_image_data):
    with pytest.raises(ValueError):
        imgparse.get_roll_pitch_yaw()

    with pytest.raises(ValueError):
        imgparse.get_roll_pitch_yaw(bad_data[0])

    with pytest.raises(ValueError):
        imgparse.get_roll_pitch_yaw(exif_data=bad_data[1])

    with pytest.raises(ValueError):
        imgparse.get_roll_pitch_yaw(xmp_data=bad_data[2])

    with pytest.raises(ValueError):
        imgparse.get_roll_pitch_yaw(bad_data[0], exif_data=bad_data[1])

    with pytest.raises(ValueError):
        imgparse.get_roll_pitch_yaw(bad_data[0], xmp_data=bad_data[2])

    with pytest.raises(ParsingError):
        imgparse.get_roll_pitch_yaw(exif_data=bad_data[1], xmp_data=bad_data[2])

    with pytest.raises(ParsingError):
        imgparse.get_roll_pitch_yaw(
            bad_data[0], exif_data=bad_data[1], xmp_data=bad_data[2]
        )

    dji_image_data[1]["Image Make"].values = "Bad Make"
    with pytest.raises(ParsingError):
        imgparse.get_roll_pitch_yaw(
            exif_data=dji_image_data[1], xmp_data=dji_image_data[2]
        )


def test_get_roll_pitch_yaw_sentera(sentera_image_data):
    roll1, pitch1, yaw1 = imgparse.get_roll_pitch_yaw(sentera_image_data[0])
    roll2, pitch2, yaw2 = imgparse.get_roll_pitch_yaw(
        sentera_image_data[0], xmp_data=sentera_image_data[2]
    )
    roll3, pitch3, yaw3 = imgparse.get_roll_pitch_yaw(
        sentera_image_data[0], exif_data=sentera_image_data[1]
    )
    roll4, pitch4, yaw4 = imgparse.get_roll_pitch_yaw(
        exif_data=sentera_image_data[1], xmp_data=sentera_image_data[2]
    )
    roll5, pitch5, yaw5 = imgparse.get_roll_pitch_yaw(
        sentera_image_data[0],
        exif_data=sentera_image_data[1],
        xmp_data=sentera_image_data[2],
    )

    assert [roll1, pitch1, yaw1] == pytest.approx(
        [-2.445596, 1.003452, 29.639198], abs=1e-06
    )
    assert [roll2, pitch2, yaw2] == pytest.approx(
        [-2.445596, 1.003452, 29.639198], abs=1e-06
    )
    assert [roll3, pitch3, yaw3] == pytest.approx(
        [-2.445596, 1.003452, 29.639198], abs=1e-06
    )
    assert [roll4, pitch4, yaw4] == pytest.approx(
        [-2.445596, 1.003452, 29.639198], abs=1e-06
    )
    assert [roll5, pitch5, yaw5] == pytest.approx(
        [-2.445596, 1.003452, 29.639198], abs=1e-06
    )


def test_get_roll_pitch_yaw_dji(dji_image_data):
    roll1, pitch1, yaw1 = imgparse.get_roll_pitch_yaw(image_path=dji_image_data[0])
    roll2, pitch2, yaw2 = imgparse.get_roll_pitch_yaw(
        dji_image_data[0], xmp_data=dji_image_data[2]
    )
    roll3, pitch3, yaw3 = imgparse.get_roll_pitch_yaw(
        dji_image_data[0], exif_data=dji_image_data[1]
    )
    roll4, pitch4, yaw4 = imgparse.get_roll_pitch_yaw(
        exif_data=dji_image_data[1], xmp_data=dji_image_data[2]
    )
    roll5, pitch5, yaw5 = imgparse.get_roll_pitch_yaw(
        dji_image_data[0], exif_data=dji_image_data[1], xmp_data=dji_image_data[2]
    )

    assert [roll1, pitch1, yaw1] == pytest.approx([0, 0.1, 90.2], abs=1e-06)
    assert [roll2, pitch2, yaw2] == pytest.approx([0, 0.1, 90.2], abs=1e-06)
    assert [roll3, pitch3, yaw3] == pytest.approx([0, 0.1, 90.2], abs=1e-06)
    assert [roll4, pitch4, yaw4] == pytest.approx([0, 0.1, 90.2], abs=1e-06)
    assert [roll5, pitch5, yaw5] == pytest.approx([0, 0.1, 90.2], abs=1e-06)


def test_get_dimensions_invalid(bad_data):
    with pytest.raises(ValueError):
        imgparse.get_dimensions()

    with pytest.raises(ValueError):
        imgparse.get_dimensions(bad_data[0])

    with pytest.raises(ParsingError):
        imgparse.get_dimensions(exif_data=bad_data[1])

    with pytest.raises(ParsingError):
        imgparse.get_dimensions(bad_data[0], exif_data=bad_data[1])


def test_get_dimensions_sentera(sentera_image_data):
    height1, width1 = imgparse.get_dimensions(sentera_image_data[0])
    height2, width2 = imgparse.get_dimensions(exif_data=sentera_image_data[1])
    height3, width3 = imgparse.get_dimensions(
        sentera_image_data[0], exif_data=sentera_image_data[1]
    )

    assert [height1, width1] == [3000, 4000]
    assert [height2, width2] == [3000, 4000]
    assert [height3, width3] == [3000, 4000]


def test_get_dimensions_dji(dji_image_data):
    height1, width1 = imgparse.get_dimensions(dji_image_data[0])
    height2, width2 = imgparse.get_dimensions(exif_data=dji_image_data[1])
    height3, width3 = imgparse.get_dimensions(
        dji_image_data[0], exif_data=dji_image_data[1]
    )

    assert [height1, width1] == [3648, 4864]
    assert [height2, width2] == [3648, 4864]
    assert [height3, width3] == [3648, 4864]


def test_get_autoexposure_sentera(sentera_image_data):
    autoexposure1 = imgparse.get_autoexposure(sentera_image_data[0])
    autoexposure2 = imgparse.get_autoexposure(exif_data=sentera_image_data[1])
    autoexposure3 = imgparse.get_autoexposure(
        sentera_image_data[0], exif_data=sentera_image_data[1]
    )

    assert autoexposure1 == pytest.approx(0.4105, rel=0.001)
    assert autoexposure2 == pytest.approx(0.4105, rel=0.001)
    assert autoexposure3 == pytest.approx(0.4105, rel=0.001)


def test_get_autoexposure_dji(dji_image_data):
    autoexposure1 = imgparse.get_autoexposure(dji_image_data[0])
    autoexposure2 = imgparse.get_autoexposure(exif_data=dji_image_data[1])
    autoexposure3 = imgparse.get_autoexposure(
        dji_image_data[0], exif_data=dji_image_data[1]
    )

    assert autoexposure1 == pytest.approx(0.0800, rel=0.001)
    assert autoexposure2 == pytest.approx(0.0800, rel=0.001)
    assert autoexposure3 == pytest.approx(0.0800, rel=0.001)


def test_get_timestamp_sentera(sentera_image_data):
    timestamp1 = imgparse.get_timestamp(sentera_image_data[0])
    timestamp2 = imgparse.get_timestamp(exif_data=sentera_image_data[1])
    timestamp3 = imgparse.get_timestamp(
        sentera_image_data[0], exif_data=sentera_image_data[1]
    )

    assert abs(
        timestamp1 - datetime.strptime("2019:03:02 22:44:46", "%Y:%m:%d %H:%M:%S")
    ) < timedelta(seconds=1)
    assert abs(
        timestamp2 - datetime.strptime("2019:03:02 22:44:46", "%Y:%m:%d %H:%M:%S")
    ) < timedelta(seconds=1)
    assert abs(
        timestamp3 - datetime.strptime("2019:03:02 22:44:46", "%Y:%m:%d %H:%M:%S")
    ) < timedelta(seconds=1)


def test_get_timestamp_dji(dji_image_data):
    timestamp1 = imgparse.get_timestamp(dji_image_data[0])
    timestamp2 = imgparse.get_timestamp(exif_data=dji_image_data[1])
    timestamp3 = imgparse.get_timestamp(dji_image_data[0], exif_data=dji_image_data[1])

    assert abs(
        timestamp1 - datetime.strptime("2018:05:22 12:03:27", "%Y:%m:%d %H:%M:%S")
    ) < timedelta(seconds=1)
    assert abs(
        timestamp2 - datetime.strptime("2018:05:22 12:03:27", "%Y:%m:%d %H:%M:%S")
    ) < timedelta(seconds=1)
    assert abs(
        timestamp3 - datetime.strptime("2018:05:22 12:03:27", "%Y:%m:%d %H:%M:%S")
    ) < timedelta(seconds=1)


def test_get_ils_6x(sentera_6x_image_data):
    ils1 = imgparse.get_ils(sentera_6x_image_data[0])
    ils2 = imgparse.get_ils(xmp_data=sentera_6x_image_data[2])
    ils3 = imgparse.get_ils(sentera_6x_image_data[0], xmp_data=sentera_6x_image_data[2])

    assert ils1 == 10532.165
    assert ils2 == 10532.165
    assert ils3 == 10532.165


def test_get_ils_non6x(dji_image_data):
    with pytest.raises(ParsingError):
        imgparse.get_ils(dji_image_data[0])

    with pytest.raises(ParsingError):
        imgparse.get_ils(xmp_data=dji_image_data[2])

    with pytest.raises(ParsingError):
        imgparse.get_ils(dji_image_data[0], xmp_data=dji_image_data[2])


def test_get_version_dji(dji_image_data):
    version1 = imgparse.get_firmware_version(dji_image_data[0])
    version2 = imgparse.get_firmware_version(
        dji_image_data[0], exif_data=dji_image_data[1]
    )
    version3 = imgparse.get_firmware_version(exif_data=dji_image_data[1])

    assert version1 == (1, 7, 1641)
    assert version2 == (1, 7, 1641)
    assert version3 == (1, 7, 1641)


def test_get_version_sentera(sentera_image_data):
    version1 = imgparse.get_firmware_version(sentera_image_data[0])
    version2 = imgparse.get_firmware_version(
        sentera_image_data[0], exif_data=sentera_image_data[1]
    )
    version3 = imgparse.get_firmware_version(exif_data=sentera_image_data[1])

    assert version1 == (0, 22, 3)
    assert version2 == (0, 22, 3)
    assert version3 == (0, 22, 3)


def test_bad_version(dji_image_data):
    dji_image_data[1]["Image Software"].values = "Bad Version"
    with pytest.raises(ParsingError):
        imgparse.get_firmware_version(exif_data=dji_image_data[1])


def test_bad_autoexposure(dji_image_data):
    dji_image_data[1].pop("EXIF ISOSpeedRatings")
    with pytest.raises(ParsingError):
        imgparse.get_autoexposure(exif_data=dji_image_data[1])


def test_bad_timestamp(dji_image_data):
    dji_image_data[1]["EXIF DateTimeOriginal"].values = "Bad Timestamp"
    with pytest.raises(ValueError):
        imgparse.get_timestamp(exif_data=dji_image_data[1])

    dji_image_data[1].pop("EXIF DateTimeOriginal")
    with pytest.raises(ParsingError):
        imgparse.get_timestamp(exif_data=dji_image_data[1])


def test_bad_pixel_pitch(dji_image_data):
    dji_image_data[1]["Image Model"].values = "Bad Model"
    with pytest.raises(ParsingError):
        imgparse.get_pixel_pitch(exif_data=dji_image_data[1])
