import dataclasses
from typing import Optional, Tuple, List, Dict, Union

import numpy as np
import pandas as pd
from numpy import dtype
import sklearn

from evidently import ColumnMapping
from evidently.analyzers.classification_performance_analyzer import ConfusionMatrix
from evidently.analyzers.utils import calculate_confusion_by_classes
from evidently.metrics.base_metric import InputData
from evidently.metrics.base_metric import Metric


@dataclasses.dataclass
class DatasetClassificationPerformanceMetrics:
    """Class for performance metrics values"""

    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    log_loss: float
    metrics_matrix: dict
    confusion_matrix: ConfusionMatrix
    confusion_by_classes: Dict[str, Dict[str, int]]
    roc_aucs: Optional[list] = None
    roc_curve: Optional[dict] = None
    pr_curve: Optional[dict] = None
    pr_table: Optional[Union[dict, list]] = None


@dataclasses.dataclass
class ClassificationPerformanceMetricsResults:
    current_metrics: DatasetClassificationPerformanceMetrics
    current_by_k_metrics: Dict[Union[int, float], DatasetClassificationPerformanceMetrics]
    current_by_threshold_metrics: Dict[Union[int, float], DatasetClassificationPerformanceMetrics]
    dummy_metrics: DatasetClassificationPerformanceMetrics
    reference_metrics: Optional[DatasetClassificationPerformanceMetrics] = None
    reference_by_k_metrics: Optional[Dict[Union[int, float], DatasetClassificationPerformanceMetrics]] = None
    reference_by_threshold_metrics: Optional[Dict[Union[int, float], DatasetClassificationPerformanceMetrics]] = None


def k_probability_threshold(prediction_probas: pd.DataFrame,
                            labels: List[str],
                            k: Union[int, float]) -> float:
    probas = prediction_probas.iloc[:, 0].sort_values(ascending=False)
    if isinstance(k, float):
        if k < 0.0 or k > 1.0:
            raise ValueError(f"K should be in range [0.0, 1.0] but was {k}")
        return probas.iloc[max(int(np.ceil(k * prediction_probas.shape[0])) - 1, 0)]
    if isinstance(k, int):
        return probas.iloc[min(k, prediction_probas.shape[0] - 1)]
    raise ValueError(f"K has unexpected type {type(k)}")


def threshold_probability_labels(prediction_probas: pd.DataFrame,
                                 pos_label: str,
                                 neg_label: str,
                                 threshold: float) -> pd.Series:
    return prediction_probas[pos_label].apply(lambda x: pos_label if x >= threshold else neg_label)


def _calculate_k_variants(
        target_data: pd.Series,
        prediction_probas: pd.DataFrame,
        labels: List[str],
        k_variants: List[Union[int, float]]):
    by_k_results = {}
    for k in k_variants:
        # calculate metrics matrix
        if prediction_probas is None or len(labels) > 2:
            raise ValueError("Top K parameter can be used only with binary classification with probas")
        pos_label, neg_label = prediction_probas.columns
        prediction_labels = threshold_probability_labels(prediction_probas, 
                                                         pos_label,
                                                         neg_label,
                                                         k_probability_threshold(prediction_probas, labels, k))
        by_k_results[k] = classification_performance_metrics(target_data, prediction_labels, prediction_probas, labels,
                                                             pos_label)
    return by_k_results


def _calculate_thresholds(
        target_data: pd.Series,
        prediction_probas: pd.DataFrame,
        labels: List[str],
        thresholds: List[float]):
    by_threshold_results = {}
    for threshold in thresholds:
        pos_label, neg_label = prediction_probas.columns
        prediction_labels = threshold_probability_labels(prediction_probas, pos_label, neg_label, threshold)
        by_threshold_results[threshold] = classification_performance_metrics(target_data,
                                                                             prediction_labels,
                                                                             prediction_probas,
                                                                             labels,
                                                                             pos_label)
    return by_threshold_results

import logging
def classification_performance_metrics(
        target: pd.Series,
        prediction: pd.Series,
        prediction_probas: Optional[pd.DataFrame],
        target_names: Optional[List[str]],
        pos_label: Optional[Union[str, int]]
) -> DatasetClassificationPerformanceMetrics:

    class_num = target.nunique()
    prediction_labels = prediction
    if class_num > 2:
        accuracy_score = sklearn.metrics.accuracy_score(target, prediction_labels)
        avg_precision = sklearn.metrics.precision_score(target, prediction_labels, average="macro")
        avg_recall = sklearn.metrics.recall_score(target, prediction_labels, average="macro")
        avg_f1 = sklearn.metrics.f1_score(target, prediction_labels, average="macro")
    else:
        accuracy_score = sklearn.metrics.accuracy_score(target, prediction_labels)
        avg_precision = sklearn.metrics.precision_score(target, prediction_labels, average="binary",
                                                        pos_label=pos_label)
        avg_recall = sklearn.metrics.recall_score(target, prediction_labels, average="binary", pos_label=pos_label)
        avg_f1 = sklearn.metrics.f1_score(target, prediction_labels, average="binary", pos_label=pos_label)

    # calculate metrics matrix
    # labels = target_names if target_names else sorted(set(target.unique()) | set(prediction.unique()))
        # binaraized_target = (target.values.reshape(-1, 1) == labels).astype(int)

    # prediction_labels = prediction

    # labels = sorted(set(target))

    if prediction_probas is not None:
        binaraized_target = (target.values.reshape(-1, 1) == list(prediction_probas.columns)).astype(int)
        array_prediction = prediction_probas.to_numpy()
        roc_auc = sklearn.metrics.roc_auc_score(binaraized_target, array_prediction, average="macro")
        log_loss = sklearn.metrics.log_loss(binaraized_target, array_prediction)
        roc_aucs = sklearn.metrics.roc_auc_score(binaraized_target, array_prediction, average=None).tolist()
        # roc curve
        roc_curve = {}
        binaraized_target = pd.DataFrame(binaraized_target)
        binaraized_target.columns = list(prediction_probas.columns)
        for label in binaraized_target.columns:
            fpr, tpr, thrs = sklearn.metrics.roc_curve(binaraized_target[label], prediction_probas[label])
            roc_curve[label] = {
                'fpr': fpr.tolist(),
                'tpr': tpr.tolist(),
                'thrs': thrs.tolist()
            }

    else:
        roc_aucs = None
        roc_auc = None
        log_loss = None
        roc_curve = None

    # calculate class support and metrics matrix
    metrics_matrix = sklearn.metrics.classification_report(target, prediction_labels, output_dict=True)

    # calculate confusion matrix
    # labels = target_names if target_names else sorted(set(target.unique()) | set(prediction.unique()))
    labels = sorted(set(target.unique()))
    conf_matrix = sklearn.metrics.confusion_matrix(target, prediction_labels)
    confusion_by_classes = calculate_confusion_by_classes(conf_matrix, labels)

    return DatasetClassificationPerformanceMetrics(
        accuracy=accuracy_score,
        precision=avg_precision,
        recall=avg_recall,
        f1=avg_f1,
        roc_auc=roc_auc,
        log_loss=log_loss,
        metrics_matrix=metrics_matrix,
        confusion_matrix=ConfusionMatrix(labels=labels, values=conf_matrix.tolist()),
        roc_aucs=roc_aucs,
        roc_curve=roc_curve,
        confusion_by_classes=confusion_by_classes,
    )


class ClassificationPerformanceMetrics(Metric[ClassificationPerformanceMetricsResults]):
    k_variants: List[Union[int, float]]
    thresholds: List[float]

    def __init__(self):
        self.k_variants = []
        self.thresholds = []

    def with_k(self, k: Union[int, float]) -> 'ClassificationPerformanceMetrics':
        self.k_variants.append(k)
        return self

    def with_threshold(self, threshold: float) -> 'ClassificationPerformanceMetrics':
        self.thresholds.append(threshold)
        return self

    def calculate(self, data: InputData, metrics: dict) -> ClassificationPerformanceMetricsResults:
        if data.current_data is None:
            raise ValueError("current dataset should be present")

        current_data = _cleanup_data(data.current_data, data.column_mapping)
        target_data = current_data[data.column_mapping.target]
        prediction_data, prediction_probas = get_prediction_data(current_data, data.column_mapping)

        target_names = data.column_mapping.target_names
        # labels = sorted(target_names if target_names else
        #                 sorted(set(target_data.unique()) | set(prediction_data.unique())))
        labels = sorted(set(target_data.unique()))
        current_metrics = classification_performance_metrics(target_data, prediction_data, prediction_probas, labels,
                                                             data.column_mapping.pos_label)

        current_by_k_metrics = _calculate_k_variants(
            target_data,
            prediction_probas,
            labels,
            self.k_variants)

        current_by_thresholds_metrics = _calculate_thresholds(
            target_data,
            prediction_probas,
            labels,
            self.thresholds)

        reference_metrics = None
        reference_by_k = None
        reference_by_threshold = None
        if data.reference_data is not None:
            reference_data = _cleanup_data(data.reference_data, data.column_mapping)
            ref_prediction_data, ref_probas = get_prediction_data(reference_data, data.column_mapping)
            ref_target = reference_data[data.column_mapping.target]
            reference_metrics = classification_performance_metrics(
                ref_target,
                ref_prediction_data,
                ref_probas,
                target_names,
                data.column_mapping.pos_label,
            )
            reference_by_k = _calculate_k_variants(ref_target, ref_probas, labels, self.k_variants)
            reference_by_threshold = _calculate_thresholds(ref_target, ref_probas, labels, self.thresholds)

        dummy_preds = pd.Series([target_data.value_counts().idxmax()] * len(target_data))
        dummy_metrics = classification_performance_metrics(
            target_data, dummy_preds, None, target_names, data.column_mapping.pos_label
        )
        dummy_metrics.roc_auc = 0.5
        return ClassificationPerformanceMetricsResults(
            current_metrics=current_metrics,
            current_by_k_metrics=current_by_k_metrics,
            current_by_threshold_metrics=current_by_thresholds_metrics,
            reference_metrics=reference_metrics,
            reference_by_k_metrics=reference_by_k,
            reference_by_threshold_metrics=reference_by_threshold,
            dummy_metrics=dummy_metrics,
        )


def _cleanup_data(data: pd.DataFrame, mapping: ColumnMapping) -> pd.DataFrame:
    target = mapping.target
    prediction = mapping.prediction
    subset = []
    if target is not None:
        subset.append(target)
    if prediction is not None and isinstance(prediction, list):
        subset += prediction
    if prediction is not None and isinstance(prediction, str):
        subset.append(prediction)
    if len(subset) > 0:
        return data.replace([np.inf, -np.inf], np.nan).dropna(axis=0, how="any", subset=subset)
    return data


def get_prediction_data(
        data: pd.DataFrame,
        mapping: ColumnMapping,
        threshold: float = 0.5) -> Tuple[pd.Series, Optional[pd.DataFrame]]:
# for binary prediction_probas has column order [pos_label, neg_label]
    # multiclass + probas
    if (
            isinstance(mapping.prediction, list)
            and len(mapping.prediction) > 2
    ):
        # list of columns with prediction probas, should be same as target labels
        return data[mapping.prediction].idxmax(axis=1), data[mapping.prediction]

    # binary + probas
    if (
            isinstance(mapping.prediction, list)
            and len(mapping.prediction) == 2
    ):
        labels = data[mapping.target].unique()
        if mapping.pos_label not in labels:
            raise ValueError("Undefined pos_label.")
        neg_label = labels[labels != mapping.pos_label][0]
        predictions = threshold_probability_labels(data[mapping.prediction], mapping.pos_label, neg_label, threshold)
        return predictions, data[[mapping.pos_label, neg_label]]

    # binary str target + one column probas
    if (
            isinstance(mapping.prediction, str)
            and (data[mapping.target].dtype == dtype("str") or data[mapping.target].dtype == dtype("object"))
            and data[mapping.prediction].dtype == dtype("float")
    ):
        labels = data[mapping.target].unique()
        if mapping.pos_label not in labels:
            raise ValueError("Undefined pos_label.")
        if mapping.prediction not in labels:
            raise ValueError(
                "No prediction for the target labels were found. "
                "Consider to rename columns with the prediction to match target labels."
            )
        neg_label = labels[labels != mapping.pos_label][0]
        if mapping.pos_label == mapping.prediction:
            pos_preds = data[mapping.prediction]
        else:
            pos_preds = data[mapping.prediction].apply(lambda x: 1.0 - x)
        prediction_probas = pd.DataFrame.from_dict(
            {
                mapping.pos_label: pos_preds,
                neg_label: pos_preds.apply(lambda x: 1.0 - x),
            }
        )
        logging.warning(prediction_probas)
        logging.warning(mapping.pos_label)
        logging.warning(neg_label)
        predictions = threshold_probability_labels(prediction_probas, mapping.pos_label, neg_label, threshold)
        
        return predictions, prediction_probas
    
    # binary target and preds are numbers and prediction is a label
    if (
        not isinstance(mapping.prediction, list)
        and mapping.prediction in [0, 1, '0', '1']
        and mapping.pos_label == 0
    ):
        if mapping.prediction in [0, "0"]:
            pos_preds = data[mapping.prediction]
        else:
            pos_preds = data[mapping.prediction].apply(lambda x: 1.0 - x)
        predictions = pos_preds >= threshold
        prediction_probas = pd.DataFrame.from_dict(
            {
                0: pos_preds,
                1: pos_preds.apply(lambda x: 1.0 - x),
            }
        )

    # binary target and preds are numbers
    if (
            isinstance(mapping.prediction, str)
            and data[mapping.target].dtype == dtype("int")
            and data[mapping.prediction].dtype == dtype("float")
    ):
        predictions = data[mapping.prediction] >= threshold
        prediction_probas = pd.DataFrame.from_dict(
            {
                1: data[mapping.prediction],
                0: data[mapping.prediction].apply(lambda x: 1.0 - x),
            }
        )
        return predictions, prediction_probas
    return data[mapping.prediction], None
