"""Integration test for dicom_image_pii_verify_engine

Note we are not checking exact pixel data for the returned image
because that is covered by testing of the "verify" function in
the original parent ImagePiiVerifyEngine class.
"""
import PIL
import pydicom

from presidio_image_redactor import DicomImagePiiVerifyEngine, BboxProcessor
import pytest

PADDING_WIDTH = 25


@pytest.fixture(scope="function")
def mock_engine():
    """Instance of the DicomImagePiiVerifyEngine"""
    # Arrange

    # Act
    dicom_image_pii_verify_engine = DicomImagePiiVerifyEngine()

    return dicom_image_pii_verify_engine


def test_verify_correctly(
    mock_engine: DicomImagePiiVerifyEngine,
    get_mock_dicom_instance: pydicom.dataset.FileDataset,
    get_mock_dicom_verify_results: dict,
):
    """Test the verify_dicom_instance function.

    Args:
        mock_engine (DicomImagePiiVerifyEngine): Instantiated engine.
        get_mock_dicom_instance (pydicom.dataset.FileDataset): Loaded DICOM.
        get_mock_dicom_verify_results (dict): Dictionary with loaded results.
    """
    # Assign
    bbox_processor = BboxProcessor()
    expected_ocr_results = get_mock_dicom_verify_results["ocr_results_formatted"]
    expected_analyzer_results = get_mock_dicom_verify_results["analyzer_results"]
    expected_ocr_results_labels = []
    for item in expected_ocr_results:
        expected_ocr_results_labels.append(item["label"])

    # Act
    (
        test_image,
        test_ocr_results,
        test_analyzer_results,
    ) = mock_engine.verify_dicom_instance(get_mock_dicom_instance, PADDING_WIDTH)
    test_ocr_results_formatted = bbox_processor.get_bboxes_from_ocr_results(
        test_ocr_results
    )
    test_analyzer_results_formatted = bbox_processor.get_bboxes_from_analyzer_results(
        test_analyzer_results
    )

    # Check most OCR results (labels) are the same
    # Don't worry about position since that is implied in analyzer results
    test_ocr_results_labels = []
    for item in test_ocr_results_formatted:
        test_ocr_results_labels.append(item["label"])
    common_labels = set(expected_ocr_results_labels).intersection(
        set(test_ocr_results_labels)
    )
    all_labels = set(expected_ocr_results_labels).union(set(test_ocr_results_labels))

    # Assert
    assert type(test_image) == PIL.Image.Image
    assert len(common_labels) / len(all_labels) >= 0.5
    assert test_analyzer_results_formatted == expected_analyzer_results


def test_eval_dicom_correctly(
    mock_engine: DicomImagePiiVerifyEngine,
    get_mock_dicom_instance: pydicom.dataset.FileDataset,
    get_mock_dicom_verify_results: dict,
):
    """Test the eval_dicom_instance function

    Args:
        mock_engine (DicomImagePiiVerifyEngine): Instantiated engine.
        get_mock_dicom_instance (pydicom.dataset.FileDataset): Loaded DICOM.
        get_mock_dicom_verify_results (dict): Dictionary with loaded results.
    """
    # Assign
    tolerance = 50
    ground_truth = get_mock_dicom_verify_results["ground_truth"]
    expected_results = {
        "all_positives": get_mock_dicom_verify_results["all_pos"],
        "ground_truth": ground_truth,
        "precision": 1.0,
        "recall": 1.0,
    }

    # Act
    test_image, test_eval_results = mock_engine.eval_dicom_instance(
        get_mock_dicom_instance, ground_truth, PADDING_WIDTH, tolerance, True
    )

    # Assert
    assert type(test_image) == PIL.Image.Image
    assert test_eval_results == expected_results
