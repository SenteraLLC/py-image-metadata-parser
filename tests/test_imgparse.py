from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import pytz
from requests_mock import Mocker

from imgparse import MetadataParser, ParsingError, TerrainAPIError
from imgparse.altitude import TERRAIN_URL, hit_terrain_api, parse_session_alt
from imgparse.types import AltitudeSource

base_path = Path(__file__).parent / "data"


class Tag:
    def __init__(self, values: Any):
        self.values = values


@pytest.fixture
def bad_data_parser() -> MetadataParser:
    parser = MetadataParser(base_path / "BAD_IMG.jpg")
    parser._exif_data = {"BadKey1": "BadValue1", "BadKey2": 0}
    parser._xmp_data = {"Bad Key1": "Bad Value1"}
    return parser


@pytest.fixture
def bad_sentera_parser() -> MetadataParser:
    parser = MetadataParser(str(base_path / "BAD_IMG.jpg"))
    parser._exif_data = {
        "BadKey1": "BadValue1",
        "BadKey2": 0,
        "Image Make": Tag("Sentera"),
        "Image Model": Tag("Blah"),
    }
    parser._xmp_data = {"Bad Key1": "Bad Value1"}
    return parser


@pytest.fixture
def bad_dji_parser() -> MetadataParser:
    parser = MetadataParser(base_path / "BAD_IMG.png")
    parser._exif_data = {
        "BadKey1": "BadValue1",
        "BadKey2": 0,
        "Image Make": Tag("DJI"),
        "Image Model": Tag("Blah"),
        "Image Software": Tag("Blah"),
    }
    parser._xmp_data = {"Bad Key1": "Bad Value1", "drone-dji:SelfData": "Blah"}
    return parser


@pytest.fixture
def fake_make_parser() -> MetadataParser:
    parser = MetadataParser(base_path / "BAD_IMG.jpg")
    parser._exif_data = {
        "BadKey1": "BadValue1",
        "BadKey2": 0,
        "Image Make": Tag("Blah"),
        "Image Model": Tag("Blah"),
    }
    parser._xmp_data = {"Bad Key1": "Bad Value1"}
    return parser


@pytest.fixture
def sentera_parser() -> MetadataParser:
    return MetadataParser(base_path / "sentera_normal.jpg")


@pytest.fixture
def dji_parser() -> MetadataParser:
    return MetadataParser(base_path / "DJI_normal.JPG")


@pytest.fixture
def dji_homepoint_parser() -> MetadataParser:
    return MetadataParser(base_path / "DJI_home_point.jpg")


@pytest.fixture
def dji_ms_parser() -> MetadataParser:
    return MetadataParser(base_path / "DJI_ms.tif")


@pytest.fixture
def micasense_ms_parser() -> MetadataParser:
    return MetadataParser(base_path / "MicaSense_ms.tif")


@pytest.fixture
def parrot_ms_parser() -> MetadataParser:
    return MetadataParser(base_path / "Parrot_ms.TIF")


@pytest.fixture
def sentera_homepoint_parser() -> MetadataParser:
    return MetadataParser(base_path / "IMG_00001.jpg")


@pytest.fixture
def sentera_6x_parser() -> MetadataParser:
    return MetadataParser(base_path / "sentera_6x.tif")


@pytest.fixture
def sentera_6x_rgb_parser() -> MetadataParser:
    return MetadataParser(base_path / "sentera_6x_rgb.jpg")


@pytest.fixture
def sentera_quad_parser() -> MetadataParser:
    return MetadataParser(base_path / "sentera_quad.jpg")


@pytest.fixture
def sentera_65r_parser() -> MetadataParser:
    return MetadataParser(base_path / "sentera_65r.jpg")


@pytest.fixture
def s3_image_parser() -> MetadataParser:
    return MetadataParser(
        "s3://bucket_name/image.jpg", "arn:aws:iam::123456789012:role/example-role"
    )


def test_get_camera_params_dji(dji_parser: MetadataParser) -> None:
    pitch1 = dji_parser.pixel_pitch_meters()
    focal1 = dji_parser.focal_length_meters()
    focal2 = dji_parser.focal_length_meters(use_calibrated=True)
    focal_pixels = dji_parser.focal_length_pixels()

    assert focal1 == 0.0088
    assert pitch1 == 2.41e-06
    assert focal2 == pytest.approx(3.666666, abs=1e-06)
    assert focal_pixels == pytest.approx(3651.4523, abs=1e-04)


def test_get_camera_params_sentera(sentera_parser: MetadataParser) -> None:
    focal1 = sentera_parser.focal_length_meters()
    focal2 = sentera_parser.focal_length_meters(use_calibrated=True)
    pitch = sentera_parser.pixel_pitch_meters()
    focal_pixels = sentera_parser.focal_length_pixels()

    assert focal1 == 0.025
    assert focal2 == 0.025
    assert pitch == pytest.approx(1.55e-06, abs=1e-06)
    assert focal_pixels == pytest.approx(16129.032, abs=1e-03)


def test_get_camera_params_bad(
    bad_sentera_parser: MetadataParser, bad_dji_parser: MetadataParser
) -> None:
    with pytest.raises(ParsingError):
        bad_sentera_parser.pixel_pitch_meters()

    with pytest.raises(ParsingError):
        bad_sentera_parser.focal_length_meters()

    with pytest.raises(ParsingError):
        bad_dji_parser.pixel_pitch_meters()

    with pytest.raises(ParsingError):
        bad_dji_parser.focal_length_meters()


def test_get_make_and_model_dji(dji_parser: MetadataParser) -> None:
    assert [dji_parser.make(), dji_parser.model()] == ["DJI", "FC6310"]


def test_get_make_and_model_sentera(sentera_parser: MetadataParser) -> None:
    assert [sentera_parser.make(), sentera_parser.model()] == [
        "Sentera",
        "21022-06_12MP-ERS-0001",
    ]


def test_get_make_and_model_bad(bad_data_parser: MetadataParser) -> None:
    with pytest.raises(ParsingError):
        bad_data_parser.make()

    with pytest.raises(ParsingError):
        bad_data_parser.model()


def test_get_lens_model_sentera(
    sentera_parser: MetadataParser,
    sentera_6x_parser: MetadataParser,
    sentera_65r_parser: MetadataParser,
) -> None:
    lens_model1 = sentera_parser.lens_model()
    lens_model2 = sentera_6x_parser.lens_model()
    lens_model3 = sentera_65r_parser.lens_model()
    assert lens_model1 == "25.0mm-0001_0008"
    assert lens_model2 == "8.00mm-0005_0020"
    assert lens_model3 == "43.0mm-0001_0031"


def test_get_lens_model_bad(
    bad_sentera_parser: MetadataParser, bad_dji_parser: MetadataParser
) -> None:
    with pytest.raises(ParsingError):
        bad_sentera_parser.lens_model()

    with pytest.raises(ParsingError):
        bad_dji_parser.lens_model()


def test_parse_session_alt(sentera_parser: MetadataParser) -> None:
    alt = parse_session_alt(sentera_parser.image_path)
    assert alt == -0.4500


def test_get_relative_altitude_sentera(
    sentera_parser: MetadataParser, sentera_quad_parser: MetadataParser
) -> None:
    alt1 = sentera_parser.relative_altitude()
    alt2 = sentera_parser.relative_altitude(alt_source=AltitudeSource.lrf)

    alt3 = sentera_quad_parser.relative_altitude()
    alt4 = sentera_quad_parser.relative_altitude(alt_source=AltitudeSource.lrf)

    assert alt1 == 51.042
    assert alt2 == 52.041  # AltimeterCalculatedAGL
    assert alt3 == pytest.approx(41.55, abs=1e-03)
    assert alt4 == 42.46  # AltimeterCalcuatedAGL


def test_get_relative_altitude_dji(dji_parser: MetadataParser) -> None:
    alt1 = dji_parser.relative_altitude()
    alt2 = dji_parser.relative_altitude(alt_source=AltitudeSource.lrf)
    assert alt1 == 15.2
    assert alt2 == 15.2


def test_get_relative_altitude_bad(
    bad_dji_parser: MetadataParser, fake_make_parser: MetadataParser
) -> None:
    with pytest.raises(ParsingError):
        bad_dji_parser.relative_altitude()

    with pytest.raises(ParsingError):
        bad_dji_parser.relative_altitude(alt_source=AltitudeSource.terrain)

    with pytest.raises(ParsingError):
        fake_make_parser.relative_altitude(alt_source=AltitudeSource.terrain)


def test_get_altitude_msl_sentera(sentera_parser: MetadataParser) -> None:
    alt = sentera_parser.global_altitude()
    assert alt == 50.592


def test_get_altitude_msl_dji(dji_parser: MetadataParser) -> None:
    alt = dji_parser.global_altitude()
    assert alt == 282.401


def test_get_altitude_msl_bad(bad_sentera_parser: MetadataParser) -> None:
    with pytest.raises(ParsingError):
        bad_sentera_parser.global_altitude()


def test_get_gsd_sentera(sentera_parser: MetadataParser) -> None:
    gsd = sentera_parser.gsd()
    assert gsd == pytest.approx(0.00316, rel=0.01)


def test_get_gsd_dji(dji_parser: MetadataParser) -> None:
    gsd = dji_parser.gsd()
    assert gsd == pytest.approx(0.00416, rel=0.01)


def test_get_lat_lon_sentera(sentera_parser: MetadataParser) -> None:
    lat, lon = sentera_parser.location()
    assert [lat, lon] == pytest.approx([27.564768, -97.657411], abs=1e-06)


def test_get_lat_lon_dji(dji_parser: MetadataParser) -> None:
    lat, lon = dji_parser.location()
    assert [lat, lon] == pytest.approx([45.514942, -93.973210], abs=1e-06)


def test_get_lat_lon_bad(bad_sentera_parser: MetadataParser) -> None:
    with pytest.raises(ParsingError):
        bad_sentera_parser.location()


def test_get_roll_pitch_yaw_sentera(sentera_parser: MetadataParser) -> None:
    roll, pitch, yaw = sentera_parser.rotation()
    assert [roll, pitch, yaw] == pytest.approx(
        [-2.445596, 1.003452, 29.639198], abs=1e-06
    )


def test_get_roll_pitch_yaw_dji(dji_parser: MetadataParser) -> None:
    roll, pitch, yaw = dji_parser.rotation()
    assert [roll, pitch, yaw] == pytest.approx([0, 0.1, 90.2], abs=1e-06)


def test_get_roll_pitch_yaw_bad(bad_sentera_parser: MetadataParser) -> None:
    with pytest.raises(ParsingError):
        bad_sentera_parser.rotation()


def test_get_dimensions_sentera(sentera_parser: MetadataParser) -> None:
    height, width = sentera_parser.dimensions()
    assert [height, width] == [3000, 4000]


def test_get_dimensions_6x(sentera_6x_parser: MetadataParser) -> None:
    height, width = sentera_6x_parser.dimensions()
    assert [height, width] == [1464, 1952]


def test_get_dimensions_6x_rgb(sentera_6x_rgb_parser: MetadataParser) -> None:
    height, width = sentera_6x_rgb_parser.dimensions()
    assert [height, width] == [3888, 5184]


def test_get_dimensions_65r(sentera_65r_parser: MetadataParser) -> None:
    height, width = sentera_65r_parser.dimensions()
    assert [height, width] == [7000, 9344]


def test_get_dimensions_dji(dji_parser: MetadataParser) -> None:
    height, width = dji_parser.dimensions()
    assert [height, width] == [3648, 4864]


def test_get_dimensions_bad(
    bad_dji_parser: MetadataParser, bad_sentera_parser: MetadataParser
) -> None:
    with pytest.raises(ParsingError):
        bad_dji_parser.dimensions()

    with pytest.raises(ParsingError):
        bad_sentera_parser.dimensions()


def test_get_principal_point_65r(sentera_65r_parser: MetadataParser) -> None:
    x, y = sentera_65r_parser.principal_point()
    height, width = sentera_65r_parser.dimensions()

    known_x_px_offset = -10.75  # checked with metashape camera calibration profile
    known_y_px_offset = -18.75

    assert [x, y] == [width / 2 + known_x_px_offset, height / 2 + known_y_px_offset]


def test_get_principal_point_bad(bad_sentera_parser: MetadataParser) -> None:
    with pytest.raises(ParsingError):
        bad_sentera_parser.principal_point()


def test_get_distortion_params_65r(sentera_65r_parser: MetadataParser) -> None:
    params = sentera_65r_parser.distortion_parameters()
    assert params == [-0.127, 0.126, 0.097, 0.0, 0.0]


def test_get_distortion_params_bad(bad_sentera_parser: MetadataParser) -> None:
    with pytest.raises(ParsingError):
        bad_sentera_parser.distortion_parameters()


def test_get_autoexposure_sentera(sentera_parser: MetadataParser) -> None:
    autoexposure = sentera_parser.autoexposure()
    assert autoexposure == pytest.approx(0.4105, rel=0.001)


def test_get_autoexposure_dji(dji_parser: MetadataParser) -> None:
    autoexposure = dji_parser.autoexposure()
    assert autoexposure == pytest.approx(0.0800, rel=0.001)


def test_get_autoexposure_bad(bad_sentera_parser: MetadataParser) -> None:
    with pytest.raises(ParsingError):
        bad_sentera_parser.autoexposure()


def test_get_timestamp_sentera(sentera_parser: MetadataParser) -> None:
    timestamp = sentera_parser.timestamp()

    correct_timestamp = datetime.strptime("2019:03:02 22:44:46", "%Y:%m:%d %H:%M:%S")
    correct_timestamp = pytz.utc.localize(correct_timestamp)

    assert abs(timestamp - correct_timestamp) < timedelta(seconds=1)


def test_get_timestamp_dji(dji_parser: MetadataParser) -> None:
    timestamp = dji_parser.timestamp()

    correct_timestamp = datetime.strptime("2018:05:22 17:03:27", "%Y:%m:%d %H:%M:%S")
    correct_timestamp = pytz.utc.localize(correct_timestamp)

    assert abs(timestamp - correct_timestamp) < timedelta(seconds=1)


def test_get_timestamp_bad(
    bad_sentera_parser: MetadataParser, sentera_parser: MetadataParser
) -> None:
    with pytest.raises(ParsingError):
        bad_sentera_parser.timestamp()

    with pytest.raises(ParsingError):
        sentera_parser.timestamp("BLAH")


def test_get_ils(
    sentera_6x_parser: MetadataParser, dji_ms_parser: MetadataParser
) -> None:
    ils = sentera_6x_parser.ils()
    assert ils == [10532.165]

    assert dji_ms_parser.ils() == [2281.689]


def test_get_ils_bad(bad_sentera_parser: MetadataParser) -> None:
    with pytest.raises(ParsingError):
        bad_sentera_parser.ils()


def test_get_version_dji(dji_parser: MetadataParser) -> None:
    version = dji_parser.firmware_version()
    assert version == (1, 7, 1641)


def test_get_version_sentera(sentera_parser: MetadataParser) -> None:
    version = sentera_parser.firmware_version()
    assert version == (0, 22, 3)


def test_get_version_bad(
    bad_sentera_parser: MetadataParser, bad_dji_parser: MetadataParser
) -> None:
    with pytest.raises(ParsingError):
        bad_sentera_parser.firmware_version()

    with pytest.raises(ParsingError):
        bad_dji_parser.firmware_version()


def test_get_bandnames(
    sentera_6x_parser: MetadataParser,
    sentera_quad_parser: MetadataParser,
    dji_ms_parser: MetadataParser,
    micasense_ms_parser: MetadataParser,
    parrot_ms_parser: MetadataParser,
) -> None:
    bandnames1 = sentera_6x_parser.bandnames()
    bandnames2 = sentera_quad_parser.bandnames()
    bandnames3 = dji_ms_parser.bandnames()
    bandnames4 = micasense_ms_parser.bandnames()
    bandnames5 = parrot_ms_parser.bandnames()

    assert bandnames1 == ["Blue"]
    assert bandnames2 == ["Red", "Green", "Blue"]
    assert bandnames3 == ["Blue"]
    assert bandnames4 == ["Blue"]
    assert bandnames5 == ["Green"]


def test_get_bandnames_bad(bad_sentera_parser: MetadataParser) -> None:
    with pytest.raises(ParsingError):
        bad_sentera_parser.bandnames()


def test_get_wavelength_data(
    sentera_6x_parser: MetadataParser,
    sentera_quad_parser: MetadataParser,
    dji_ms_parser: MetadataParser,
    micasense_ms_parser: MetadataParser,
    parrot_ms_parser: MetadataParser,
) -> None:
    central1, fwhm1 = sentera_6x_parser.wavelength_data()
    central2, fwhm2 = sentera_quad_parser.wavelength_data()
    central3, fwhm3 = dji_ms_parser.wavelength_data()
    central4, fwhm4 = micasense_ms_parser.wavelength_data()
    central5, fwhm5 = parrot_ms_parser.wavelength_data()

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


def test_get_wavelength_data_bad(bad_sentera_parser: MetadataParser) -> None:
    with pytest.raises(ParsingError):
        bad_sentera_parser.wavelength_data()


def test_dji_terrain_elevation(
    dji_homepoint_parser: MetadataParser, requests_mock: Mocker
) -> None:
    mock = requests_mock.get(
        TERRAIN_URL,
        [
            {"json": {"status": "OK", "results": [{"elevation": 50}]}},
            {"json": {"status": "OK", "results": [{"elevation": 0}]}},
        ],
    )
    alt = dji_homepoint_parser.relative_altitude(alt_source=AltitudeSource.terrain)
    assert alt == 171.4

    alt = dji_homepoint_parser.relative_altitude(alt_source=AltitudeSource.terrain)
    assert alt == 171.4
    # Make sure api calls only requested once
    assert len(mock.request_history) == 2

    # Clear lru cache to get new responses from hit_terrain_api
    hit_terrain_api.cache_clear()

    requests_mock.get(TERRAIN_URL, json={"status": "ERROR"})
    alt2 = dji_homepoint_parser.relative_altitude(alt_source=AltitudeSource.terrain)
    assert alt2 == 121.4

    with pytest.raises(TerrainAPIError):
        dji_homepoint_parser.relative_altitude(
            alt_source=AltitudeSource.terrain, fallback=False
        )


def test_sentera_terrain_elevation(
    sentera_homepoint_parser: MetadataParser, requests_mock: Mocker
) -> None:
    mock = requests_mock.get(
        TERRAIN_URL,
        [
            {"json": {"status": "OK", "results": [{"elevation": 50}]}},
            {"json": {"status": "OK", "results": [{"elevation": 0}]}},
        ],
    )
    alt = sentera_homepoint_parser.relative_altitude(alt_source=AltitudeSource.terrain)
    assert alt == pytest.approx(114.45, 0.01)

    alt = sentera_homepoint_parser.relative_altitude(alt_source=AltitudeSource.terrain)
    assert alt == pytest.approx(114.45, 0.01)

    # Make sure api calls only requested once
    assert len(mock.request_history) == 2

    # Clear lru cache to get new responses from hit_terrain_api
    hit_terrain_api.cache_clear()

    requests_mock.get(TERRAIN_URL, json={"status": "ERROR"})
    alt2 = sentera_homepoint_parser.relative_altitude(alt_source=AltitudeSource.terrain)
    assert alt2 == pytest.approx(64.45, 0.01)

    with pytest.raises(TerrainAPIError):
        sentera_homepoint_parser.relative_altitude(
            alt_source=AltitudeSource.terrain, fallback=False
        )


def test_get_serial_num_sentera(sentera_6x_parser: MetadataParser) -> None:
    serial_no = sentera_6x_parser.serial_number()
    assert serial_no == 1


def test_get_serial_bad(
    sentera_65r_parser: MetadataParser, sentera_quad_parser: MetadataParser
) -> None:
    # Non-numeric
    with pytest.raises(ParsingError):
        sentera_65r_parser.serial_number()

    # Doesn't exist
    with pytest.raises(ParsingError):
        sentera_quad_parser.serial_number()


def test_get_irradiance(
    dji_ms_parser: MetadataParser, sentera_parser: MetadataParser
) -> None:
    assert dji_ms_parser.irradiance() == 2281.688965

    with pytest.raises(ParsingError):
        sentera_parser.irradiance()


def test_get_capture_id(
    micasense_ms_parser: MetadataParser,
    dji_ms_parser: MetadataParser,
    sentera_6x_rgb_parser: MetadataParser,
    parrot_ms_parser: MetadataParser,
    sentera_parser: MetadataParser,
) -> None:
    assert micasense_ms_parser.capture_id() == "rbSiEyRnG1UCUY5EM20i"
    assert dji_ms_parser.capture_id() == "576047cc8d7411ec87fda099c9f7f1f5"
    assert sentera_6x_rgb_parser.capture_id() == "2022-11-10_22-03-47_8"
    assert parrot_ms_parser.capture_id() == "15B9793D3A9597E2E348B932826B427B"

    with pytest.raises(ParsingError):
        sentera_parser.capture_id()


@patch("imgparse.util.s3_resource")
@patch("imgparse.util.exifread.process_file")
def test_get_make_and_model_s3(
    mock_process_file: MagicMock,
    mock_s3_resource: MagicMock,
    s3_image_parser: MetadataParser,
) -> None:
    mock_s3_client = MagicMock()
    mock_s3_object = MagicMock()

    mock_s3_client.Object.return_value = mock_s3_object
    mock_s3_object.get.return_value = {"Body": BytesIO(b"fake_exif_header_bytes")}

    mock_s3_resource.return_value = mock_s3_client

    mock_process_file.return_value = {
        "Image Make": Tag("TestMake"),
        "Image Model": Tag("TestModel"),
    }

    make, model = s3_image_parser.make(), s3_image_parser.model()

    mock_s3_client.Object.assert_called_with(
        s3_image_parser.image_path.bucket, s3_image_parser.image_path.key
    )
    mock_s3_object.get.assert_called_once_with(Range="bytes=0-65536")
    mock_process_file.assert_called_once()

    assert [make, model] == ["TestMake", "TestModel"]


@patch("imgparse.util.s3_resource")  # Mock s3_resource used in get_xmp_data()
def test_get_roll_pitch_yaw_s3(
    mock_s3_resource: MagicMock, s3_image_parser: MetadataParser
) -> None:
    # Path to the local test file with XMP data
    local_test_file = base_path / "sentera_normal.jpg"

    # Mock the S3 object and its get() method to simulate chunk reading
    mock_s3_object = MagicMock()
    with open(local_test_file, "r", encoding="latin_1") as f:
        file_content = f.read()

    # Define the behavior for the S3 get call, return the content in chunks
    def s3_chunk_side_effect(Range=None, **kwargs):  # type: ignore
        if Range:
            start_byte, end_byte = map(int, Range.replace("bytes=", "").split("-"))
            chunk = file_content[start_byte : end_byte + 1]
            return {"Body": MagicMock(read=lambda: chunk.encode("latin_1"))}
        return {"Body": MagicMock(read=lambda: b"")}

    # Set the mock to use the chunk reading side effect
    mock_s3_object.get.side_effect = s3_chunk_side_effect
    mock_s3_resource.return_value.Object.return_value = mock_s3_object

    # Invoke the function that we are testing (get_roll_pitch_yaw)
    roll, pitch, yaw = s3_image_parser.rotation()

    assert [roll, pitch, yaw] == pytest.approx(
        [-2.445596, 1.003452, 29.639198], abs=1e-06
    )

    # Test error scenario when no XMP data is found
    with pytest.raises(ParsingError):
        mock_s3_object.get.side_effect = lambda *args, **kwargs: {
            "Body": MagicMock(read=lambda: b"")
        }
        s3_image_parser._xmp_data = None
        s3_image_parser.rotation()
