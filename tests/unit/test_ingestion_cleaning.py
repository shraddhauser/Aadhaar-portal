"""Unit tests for the CSV cleaning step (no database writes)."""
import pandas as pd
import pytest

from backend.data_ingestion import DataIngestionPipeline


@pytest.fixture
def pipeline(db_session):
    return DataIngestionPipeline(db_session)


def _clean(pipeline, **columns):
    return pipeline.clean_and_normalize_enrollment_data(pd.DataFrame(columns))


LOWERCASE_GENDER_BUG = pytest.mark.xfail(
    strict=True, reason="Known bug: gender_map has 'Male'/'MALE'/'m' but not 'male', so it becomes 'Other'")
DATE_COLUMN_BUG = pytest.mark.xfail(
    strict=True, reason="Known bug: the cleaner drops the parsed enrollment_date column, then "
                        "refills it with the current time, so every row gets today's date")
PANDAS3_FILLNA_BUG = pytest.mark.xfail(
    strict=True, raises=TypeError,
    reason="Known bug: fillna(ndarray) is rejected by pandas 3.x (requirements.txt does not pin pandas)")


@pytest.mark.parametrize("raw,expected", [
    ("M", "Male"), pytest.param("male", "Male", marks=LOWERCASE_GENDER_BUG),
    ("F", "Female"), ("FEMALE", "Female"), ("O", "Other"), ("unknown", "Other"),
])
def test_gender_is_normalised(pipeline, raw, expected):
    df = _clean(pipeline, enrollment_date=["2026-01-01"], gender=[raw], age=[30],
                region_code=["MH-MUM"])
    assert df["gender"].iloc[0] == expected


@pytest.mark.parametrize("age,group", [
    (0, "0-18"), (18, "0-18"), (19, "19-35"), (35, "19-35"),
    (36, "36-60"), (60, "36-60"), (61, "60+"), (95, "60+"),
])
def test_age_is_mapped_to_group(pipeline, age, group):
    df = _clean(pipeline, enrollment_date=["2026-01-01"], gender=["Male"], age=[age],
                region_code=["MH-MUM"])
    assert df["age_group"].iloc[0] == group


@pytest.mark.parametrize("bad_age", [-1, 200, "abc"])
def test_invalid_age_currently_defaults_to_36_60(pipeline, bad_age):
    df = _clean(pipeline, enrollment_date=["2026-01-01"], gender=["Male"], age=[bad_age],
                region_code=["MH-MUM"])
    assert df["age_group"].iloc[0] == "36-60"


def test_district_is_mapped_to_region_code(pipeline):
    df = _clean(pipeline, enrollment_date=["2026-01-01"], gender=["Male"], age=[30],
                district=["Bangalore"])
    assert df["region_code"].iloc[0] == "KA-BLR"


def test_unknown_district_currently_defaults_to_mumbai(pipeline):
    df = _clean(pipeline, enrollment_date=["2026-01-01"], gender=["Male"], age=[30],
                district=["Atlantis"])
    assert df["region_code"].iloc[0] == "MH-MUM"


@DATE_COLUMN_BUG
def test_parsed_date_is_kept(pipeline):
    df = _clean(pipeline, enrollment_date=["2024-03-15"], gender=["Male"], age=[30],
                region_code=["MH-MUM"])
    assert str(df["enrollment_date"].iloc[0].date()) == "2024-03-15"


@DATE_COLUMN_BUG
def test_rows_without_a_date_are_dropped(pipeline):
    df = _clean(pipeline, enrollment_date=["2026-01-01", None], gender=["Male", "Male"],
                age=[30, 40], region_code=["MH-MUM", "MH-MUM"])
    assert len(df) == 1


@PANDAS3_FILLNA_BUG
def test_biometric_scores_are_clipped_to_0_100(pipeline):
    df = pipeline.clean_and_normalize_biometric_data(pd.DataFrame({
        "enrollment_date": ["2026-01-01", "2026-01-02"],
        "fingerprint_quality": [150, -5],
        "iris_quality": [80, 80],
        "photo_quality": [90, 90],
    }))
    assert df["fingerprint_quality"].tolist() == [100, 0]
