import json

import pandas as pd

from pytest import approx

from evidently.pipeline.column_mapping import ColumnMapping
from evidently.tests import TestAccuracyScore
from evidently.tests import TestPrecisionScore
from evidently.tests import TestF1Score
from evidently.tests import TestRecallScore
from evidently.tests import TestRocAuc
from evidently.tests import TestLogLoss
from evidently.tests import TestPrecisionByClass
from evidently.tests import TestRecallByClass
from evidently.tests import TestF1ByClass
from evidently.test_suite import TestSuite


def test_accuracy_score_test() -> None:
    test_dataset = pd.DataFrame(
        {
            "target": ["a", "a", "a", "b"],
            "prediction": ["a", "a", "b", "b"],
        }
    )
    column_mapping = ColumnMapping(pos_label="a")
    suite = TestSuite(tests=[TestAccuracyScore(lt=0.8)])
    suite.run(current_data=test_dataset, reference_data=None, column_mapping=column_mapping)
    assert suite


def test_accuracy_score_test_render_json() -> None:
    test_dataset = pd.DataFrame(
        {
            "target": [1, 0, 0, 1],
            "prediction": [1, 0, 1, 0],
        }
    )
    suite = TestSuite(tests=[TestAccuracyScore()])
    suite.run(current_data=test_dataset, reference_data=test_dataset)
    assert suite

    result_from_json = json.loads(suite.json())
    assert result_from_json["summary"]["all_passed"] is True
    test_info = result_from_json["tests"][0]
    assert test_info == {
        "description": "Accuracy Score is 0.5. Test Threshold is eq=0.5 ± 0.1",
        "group": "classification",
        "name": "Accuracy Score",
        "parameters": {"accuracy": 0.5, "condition": {"eq": {"absolute": 1e-12, "relative": 0.2, "value": 0.5}}},
        "status": "SUCCESS",
    }


def test_precision_score_test() -> None:
    test_dataset = pd.DataFrame(
        {
            "target": ["a", "a", "a", "b"],
            "prediction": ["a", "a", "b", "b"],
        }
    )
    column_mapping = ColumnMapping(pos_label="a")
    suite = TestSuite(tests=[TestPrecisionScore(gt=0.8)])
    suite.run(current_data=test_dataset, reference_data=None, column_mapping=column_mapping)
    assert suite


def test_precision_score_test_render_json() -> None:
    test_dataset = pd.DataFrame(
        {
            "target": [1, 0, 0, 1],
            "prediction": [1, 0, 1, 0],
        }
    )
    suite = TestSuite(tests=[TestPrecisionScore()])
    suite.run(current_data=test_dataset, reference_data=test_dataset)
    assert suite

    result_from_json = json.loads(suite.json())
    assert result_from_json["summary"]["all_passed"] is True
    test_info = result_from_json["tests"][0]
    assert test_info == {
        "description": "Precision Score is 0.5. Test Threshold is eq=0.5 ± 0.1",
        "group": "classification",
        "name": "Precision Score",
        "parameters": {"condition": {"eq": {"absolute": 1e-12, "relative": 0.2, "value": 0.5}}, "precision": 0.5},
        "status": "SUCCESS",
    }


def test_f1_score_test() -> None:
    test_dataset = pd.DataFrame(
        {
            "target": ["a", "a", "a", "b"],
            "prediction": ["a", "a", "b", "b"],
        }
    )
    column_mapping = ColumnMapping(pos_label="a")
    suite = TestSuite(tests=[TestF1Score(gt=0.5)])
    suite.run(current_data=test_dataset, reference_data=None, column_mapping=column_mapping)
    assert suite


def test_f1_score_test_render_json() -> None:
    test_dataset = pd.DataFrame(
        {
            "target": [1, 0, 0, 1],
            "prediction": [1, 0, 1, 0],
        }
    )
    suite = TestSuite(tests=[TestF1Score()])
    suite.run(current_data=test_dataset, reference_data=test_dataset)
    assert suite

    result_from_json = json.loads(suite.json())
    assert result_from_json["summary"]["all_passed"] is True
    test_info = result_from_json["tests"][0]
    assert test_info == {
        "description": "F1 Score is 0.5. Test Threshold is eq=0.5 ± 0.1",
        "group": "classification",
        "name": "F1 Score",
        "parameters": {"condition": {"eq": {"absolute": 1e-12, "relative": 0.2, "value": 0.5}}, "f1": 0.5},
        "status": "SUCCESS",
    }


def test_recall_score_test() -> None:
    test_dataset = pd.DataFrame(
        {
            "target": ["a", "a", "a", "b"],
            "prediction": ["a", "a", "b", "b"],
        }
    )
    column_mapping = ColumnMapping(pos_label="a")
    suite = TestSuite(tests=[TestRecallScore(lt=0.8)])
    suite.run(current_data=test_dataset, reference_data=None, column_mapping=column_mapping)
    assert suite


def test_recall_score_test_render_json() -> None:
    test_dataset = pd.DataFrame(
        {
            "target": [1, 0, 0, 1],
            "prediction": [1, 0, 1, 0],
        }
    )
    suite = TestSuite(tests=[TestRecallScore()])
    suite.run(current_data=test_dataset, reference_data=test_dataset)
    assert suite

    result_from_json = json.loads(suite.json())
    assert result_from_json["summary"]["all_passed"] is True
    test_info = result_from_json["tests"][0]
    assert test_info == {
        "description": "Recall Score is 0.5. Test Threshold is eq=0.5 ± 0.1",
        "group": "classification",
        "name": "Recall Score",
        "parameters": {"condition": {"eq": {"absolute": 1e-12, "relative": 0.2, "value": 0.5}}, "recall": 0.5},
        "status": "SUCCESS",
    }


def test_log_loss_test() -> None:
    test_dataset = pd.DataFrame(
        {
            "target": ["a", "a", "a", "b"],
            "b": [0.2, 0.5, 0.3, 0.6],
        }
    )
    column_mapping = ColumnMapping(prediction="b", pos_label="a")
    suite = TestSuite(tests=[TestLogLoss(gte=0.8)])
    suite.run(current_data=test_dataset, reference_data=None, column_mapping=column_mapping)
    assert not suite

    suite = TestSuite(tests=[TestLogLoss(lt=0.8)])
    suite.run(current_data=test_dataset, reference_data=None, column_mapping=column_mapping)
    assert suite


def test_log_loss_test_json_render() -> None:
    test_dataset = pd.DataFrame(
        {
            "target": ["a", "a", "a", "b"],
            "b": [0.2, 0.5, 0.3, 0.6],
        }
    )
    column_mapping = ColumnMapping(prediction="b", pos_label="a")
    suite = TestSuite(tests=[TestLogLoss()])
    suite.run(current_data=test_dataset, reference_data=test_dataset, column_mapping=column_mapping)
    assert suite

    result_from_json = json.loads(suite.json())
    assert result_from_json["summary"]["all_passed"] is True
    test_info = result_from_json["tests"][0]
    assert test_info == {
        "description": " Logarithmic Loss is 0.446. Test Threshold is eq=0.446 ± " "0.0892",
        "group": "classification",
        "name": "Logarithmic Loss",
        "parameters": {
            "condition": {"eq": {"absolute": 1e-12, "relative": 0.2, "value": approx(0.446, abs=0.0001)}},
            "log_loss": approx(0.446, abs=0.0001),
        },
        "status": "SUCCESS",
    }


def test_log_loss_test_cannot_calculate_log_loss() -> None:
    test_dataset = pd.DataFrame(
        {
            "target": ["a", "a", "a", "b", "b", "b", "c", "c", "c", "c"],
            "prediction": ["a", "a", "a", "b", "a", "c", "a", "c", "c", "c"],
        }
    )
    column_mapping = ColumnMapping(target="target", prediction="prediction")

    suite = TestSuite(tests=[TestLogLoss(lt=1)])
    suite.run(current_data=test_dataset, reference_data=None, column_mapping=column_mapping)
    assert not suite
    test_info = suite.as_dict()["tests"][0]
    assert test_info["description"] == "No log loss value for the data"
    assert test_info["status"] == "ERROR"


def test_roc_auc_test() -> None:
    test_dataset = pd.DataFrame(
        {
            "target": ["a", "a", "a", "b"],
            "a": [0.8, 0.5, 0.7, 0.3],
            "b": [0.2, 0.5, 0.3, 0.6],
        }
    )
    column_mapping = ColumnMapping(prediction=["a", "b"], pos_label="a")
    suite = TestSuite(tests=[TestRocAuc(gte=0.8)])
    suite.run(current_data=test_dataset, reference_data=None, column_mapping=column_mapping)
    assert suite

    suite = TestSuite(tests=[TestRocAuc(lt=0.8)])
    suite.run(current_data=test_dataset, reference_data=None, column_mapping=column_mapping)
    assert not suite


def test_roc_auc_test_json_render() -> None:
    test_dataset = pd.DataFrame(
        {
            "target": ["t", "f", "f", "t"],
            "f": [0.8, 0.5, 0.7, 0.3],
            "t": [0.2, 0.5, 0.3, 0.6],
        }
    )
    column_mapping = ColumnMapping(prediction=["f", "t"], pos_label="t")
    suite = TestSuite(tests=[TestRocAuc(lt=0.8)])
    suite.run(current_data=test_dataset, reference_data=None, column_mapping=column_mapping)
    assert suite

    result_from_json = json.loads(suite.json())
    assert result_from_json["summary"]["all_passed"] is True
    test_info = result_from_json["tests"][0]
    assert test_info == {
        "description": "ROC AUC Score is 0.5. Test Threshold is lt=0.8",
        "group": "classification",
        "name": "ROC AUC Score",
        "parameters": {"condition": {"lt": 0.8}, "roc_auc": 0.5},
        "status": "SUCCESS",
    }


def test_roc_auc_test_cannot_calculate_roc_auc() -> None:
    test_dataset = pd.DataFrame(
        {
            "target": ["a", "a", "a", "b", "b", "b", "c", "c", "c", "c"],
            "prediction": ["a", "a", "a", "b", "a", "c", "a", "c", "c", "c"],
        }
    )
    column_mapping = ColumnMapping(target="target", prediction="prediction")

    suite = TestSuite(tests=[TestRocAuc(lt=1)])
    suite.run(current_data=test_dataset, reference_data=None, column_mapping=column_mapping)
    assert not suite
    test_info = suite.as_dict()["tests"][0]
    assert test_info["description"] == "No ROC AUC Score value for the data"
    assert test_info["status"] == "ERROR"
