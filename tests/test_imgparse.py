import os
import pytest
import imgparse

base_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


@pytest.fixture
def sentera_image_data():
    sentera_image_path = os.path.join(base_path, "data", "IMG_00037.jpg")
    sentera_exif_data = imgparse.get_exif_data(sentera_image_path)
    return [sentera_image_path, sentera_exif_data]


@pytest.fixture
def dji_image_data():
    dji_image_path = os.path.join(base_path, "data", "DJI_0012.JPG")
    dji_exif_data = imgparse.get_exif_data(dji_image_path)
    return [dji_image_path, dji_exif_data]


def test_get_exif_data(sentera_image_data, dji_image_data):
    assert sentera_image_data[1] is not None
    assert dji_image_data[1] is not None


def test_get_camera_params_invalid():
    with pytest.raises(ValueError):
        focal, pitch = imgparse.get_camera_params()

    with pytest.raises(ValueError):
        focal, pitch = imgparse.get_camera_params("")

    with pytest.raises(ValueError):
        focal, pitch = imgparse.get_camera_params(exif_data={})

    with pytest.raises(ValueError):
        focal, pitch = imgparse.get_camera_params("", exif_data={})


def test_get_camera_params_dji(dji_image_data):
    focal1, pitch1 = imgparse.get_camera_params(dji_image_data[0])
    focal2, pitch2 = imgparse.get_camera_params(exif_data=dji_image_data[1])
    focal3, pitch3 = imgparse.get_camera_params(dji_image_data[0], exif_data=dji_image_data[1])

    assert focal1 == 0.0088
    assert focal2 == 0.0088
    assert focal3 == 0.0088
    assert pitch1 == 2.41e-06
    assert pitch2 == 2.41e-06
    assert pitch3 == 2.41e-06


def test_get_camera_params_sentera(sentera_image_data):
    focal1, pitch1 = imgparse.get_camera_params(sentera_image_data[0])
    focal2, pitch2 = imgparse.get_camera_params(exif_data=sentera_image_data[1])
    focal3, pitch3 = imgparse.get_camera_params(sentera_image_data[0], exif_data=sentera_image_data[1])

    assert focal1 == 0.025
    assert focal2 == 0.025
    assert focal3 == 0.025
    assert pitch1 == pytest.approx(1.55e-06)
    assert pitch2 == pytest.approx(1.55e-06)
    assert pitch3 == pytest.approx(1.55e-06)


def test_get_make_and_model_invalid():
    with pytest.raises(ValueError):
        make, model = imgparse.get_camera_params()

    with pytest.raises(ValueError):
        make, model = imgparse.get_camera_params("")

    with pytest.raises(ValueError):
        make, model = imgparse.get_camera_params(exif_data={})

    with pytest.raises(ValueError):
        make, model = imgparse.get_camera_params("", exif_data={})


def test_get_make_and_model_dji(dji_image_data):
    make1, model1 = imgparse.get_make_and_model(dji_image_data[0])
    make2, model2 = imgparse.get_make_and_model(exif_data=dji_image_data[1])
    make3, model3 = imgparse.get_make_and_model(exif_data=dji_image_data[1])

    assert make1 == 'DJI'
    assert make2 == 'DJI'
    assert make3 == 'DJI'
    assert model1 == 'FC6310'
    assert model2 == 'FC6310'
    assert model3 == 'FC6310'


def test_get_make_and_model_sentera(sentera_image_data):
    make1, model1 = imgparse.get_make_and_model(sentera_image_data[0])
    make2, model2 = imgparse.get_make_and_model(exif_data=sentera_image_data[1])
    make3, model3 = imgparse.get_make_and_model(sentera_image_data[0], exif_data=sentera_image_data[1])

    assert make1 == 'Sentera'
    assert make2 == 'Sentera'
    assert make3 == 'Sentera'
    assert model1 == '21022-06_12MP-ERS-0001'
    assert model2 == '21022-06_12MP-ERS-0001'
    assert model3 == '21022-06_12MP-ERS-0001'


def test_parse_session_alt_invalid():
    with pytest.raises(ValueError):
        alt = imgparse.parse_session_alt("")


def test_parse_session_alt(sentera_image_data):
    alt = imgparse.parse_session_alt(sentera_image_data[0])

    assert alt == -0.4500


def test_get_relative_altitude_invalid():
    with pytest.raises(ValueError):
        alt = imgparse.get_relative_altitude("")

    with pytest.raises(ValueError):
        alt = imgparse.get_relative_altitude("", exif_data={})


def test_get_altitude_msl_invalid():
    with pytest.raises(ValueError):
        alt = imgparse.get_altitude_msl()

    with pytest.raises(ValueError):
        alt = imgparse.get_altitude_msl("")

    with pytest.raises(ValueError):
        alt = imgparse.get_altitude_msl(exif_data={})

    with pytest.raises(ValueError):
        alt = imgparse.get_altitude_msl("", exif_data={})


def test_get_relative_altitude_sentera(sentera_image_data):
    alt1 = imgparse.get_relative_altitude(sentera_image_data[0])
    alt2 = imgparse.get_relative_altitude(sentera_image_data[0], exif_data=sentera_image_data[1])

    assert alt1 == 51.042
    assert alt2 == 51.042


def test_get_altitude_msl_sentera(sentera_image_data):
    alt1 = imgparse.get_altitude_msl(sentera_image_data[0])
    alt2 = imgparse.get_altitude_msl(exif_data=sentera_image_data[1])
    alt3 = imgparse.get_altitude_msl(sentera_image_data[0], exif_data=sentera_image_data[1])

    assert alt1 == 50.592
    assert alt2 == 50.592
    assert alt3 == 50.592


def test_get_relative_altitude_dji(dji_image_data):
    alt1 = imgparse.get_relative_altitude(dji_image_data[0])
    alt2 = imgparse.get_relative_altitude(dji_image_data[0], exif_data=dji_image_data[1])

    assert alt1 == 15.2
    assert alt2 == 15.2


def test_get_altitude_msl_dji(dji_image_data):
    alt1 = imgparse.get_altitude_msl(dji_image_data[0])
    alt2 = imgparse.get_altitude_msl(exif_data=dji_image_data[1])
    alt3 = imgparse.get_altitude_msl(dji_image_data[0], exif_data=dji_image_data[1])

    assert alt1 == 282.401
    assert alt2 == 282.401
    assert alt3 == 282.401


def test_get_gsd_invalid():
    with pytest.raises(ValueError):
        gsd = imgparse.get_gsd("")

    with pytest.raises(ValueError):
        gsd = imgparse.get_gsd("", exif_data={})


def test_get_gsd_sentera(sentera_image_data):
    gsd1 = imgparse.get_gsd(sentera_image_data[0])
    gsd2 = imgparse.get_gsd(sentera_image_data[0], exif_data=sentera_image_data[1])

    assert gsd1 == pytest.approx(0.00316, rel=0.01)
    assert gsd2 == pytest.approx(0.00316, rel=0.01)


def test_get_gsd_dji(dji_image_data):
    gsd1 = imgparse.get_gsd(dji_image_data[0])
    gsd2 = imgparse.get_gsd(dji_image_data[0], exif_data=dji_image_data[1])

    assert gsd1 == pytest.approx(0.00416, rel=0.01)
    assert gsd2 == pytest.approx(0.00416, rel=0.01)


def test_get_lat_lon_invalid():
    with pytest.raises(ValueError):
        lat, lon = imgparse.get_lat_lon()

    with pytest.raises(ValueError):
        lat, lon = imgparse.get_lat_lon("")

    with pytest.raises(ValueError):
        lat, lon = imgparse.get_lat_lon("", exif_data={})


def test_get_lat_lon_sentera(sentera_image_data):
    lat1, lon1 = imgparse.get_lat_lon(sentera_image_data[0])
    lat2, lon2 = imgparse.get_lat_lon(exif_data=sentera_image_data[1])
    lat3, lon3 = imgparse.get_lat_lon(sentera_image_data[0], exif_data=sentera_image_data[1])

    assert lat1 == pytest.approx(27.564768, abs=1e-06)
    assert lat2 == pytest.approx(27.564768, abs=1e-06)
    assert lat3 == pytest.approx(27.564768, abs=1e-06)
    assert lon1 == pytest.approx(-97.657411, abs=1e-06)
    assert lon2 == pytest.approx(-97.657411, abs=1e-06)
    assert lon3 == pytest.approx(-97.657411, abs=1e-06)


def test_get_lat_lon_dji(dji_image_data):
    lat1, lon1 = imgparse.get_lat_lon(dji_image_data[0])
    lat2, lon2 = imgparse.get_lat_lon(exif_data=dji_image_data[1])
    lat3, lon3 = imgparse.get_lat_lon(dji_image_data[0], exif_data=dji_image_data[1])

    assert lat1 == pytest.approx(45.514942, abs=1e-06)
    assert lat2 == pytest.approx(45.514942, abs=1e-06)
    assert lat3 == pytest.approx(45.514942, abs=1e-06)
    assert lon1 == pytest.approx(-93.973210, abs=1e-06)
    assert lon2 == pytest.approx(-93.973210, abs=1e-06)
    assert lon3 == pytest.approx(-93.973210, abs=1e-06)
