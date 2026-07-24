import numpy as np

from backend.ml.dicom_3d_segmentation import VolumetricUNet3DEngine, run_3d_dicom_segmentation


def test_volumetric_unet3d_segmentation():
    engine = VolumetricUNet3DEngine()
    vol = np.ones((32, 32, 32), dtype=np.float32) * 0.5
    res = engine.segment_volume_voxels(vol, modality="CT")
    assert res["segmentation_status"] == "success"
    assert res["volume_dimensions"] == [32, 32, 32]
    assert res["model_architecture"] == "3D_UNet_Volumetric_Segmentation"


def test_run_3d_dicom_segmentation_helper():
    info = run_3d_dicom_segmentation((16, 16, 16))
    assert info["segmentation_status"] == "success"
    assert info["volume_dimensions"] == [16, 16, 16]
