import pytest

from backend import dicomweb


def test_dicomweb_readiness_reports_configuration_without_secrets(monkeypatch):
    monkeypatch.setenv("DICOMWEB_ENABLED", "true")
    monkeypatch.setenv("DICOMWEB_BASE_URL", "https://pacs.example.com/dicomweb")
    monkeypatch.setenv("DICOMWEB_AE_TITLE", "CLINIC_AE")
    monkeypatch.setenv("DICOMWEB_BEARER_TOKEN", "dicom-secret-token")

    readiness = dicomweb.get_readiness()

    assert readiness["enabled"] is True
    assert readiness["base_url_configured"] is True
    assert readiness["ae_title_configured"] is True
    assert readiness["token_configured"] is True
    assert readiness["secrets_exposed"] is False
    assert "dicom-secret-token" not in str(readiness)
    assert readiness["capabilities"] == {
        "QIDO-RS": "study search metadata links",
        "WADO-RS": "study metadata retrieval links",
        "STOW-RS": "configured store endpoint metadata",
    }


def test_build_study_metadata_links_uses_dicomweb_paths():
    links = dicomweb.build_study_metadata_links(
        "1.2.840.10008.1",
        base_url="https://pacs.example.com/dicomweb/",
    )

    assert links["study_instance_uid"] == "1.2.840.10008.1"
    assert links["qido_rs_study_search"] == (
        "https://pacs.example.com/dicomweb/studies?StudyInstanceUID=1.2.840.10008.1"
    )
    assert links["wado_rs_study_metadata"] == (
        "https://pacs.example.com/dicomweb/studies/1.2.840.10008.1/metadata"
    )
    assert links["stow_rs_store"] == "https://pacs.example.com/dicomweb/studies"
    assert links["pixel_data_included"] is False
    assert links["pii_exposed"] is False


def test_build_study_metadata_links_rejects_unsafe_uid():
    with pytest.raises(dicomweb.DICOMwebValidationError):
        dicomweb.build_study_metadata_links(
            "1.2.bad-token",
            base_url="https://pacs.example.com/dicomweb",
        )


def test_build_study_metadata_links_requires_base_url(monkeypatch):
    monkeypatch.delenv("DICOMWEB_BASE_URL", raising=False)

    with pytest.raises(dicomweb.DICOMwebConfigurationError):
        dicomweb.build_study_metadata_links("1.2.840.10008.1")
