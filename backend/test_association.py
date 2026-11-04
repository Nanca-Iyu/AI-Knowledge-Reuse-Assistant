import unittest
from unittest.mock import patch
from fastapi import HTTPException
from server import validate_association, association, AssociationRequest


class AssociationTests(unittest.TestCase):
    def result(self, **changes):
        value = dict(relation="关联及局限", sufficient=True, author_method=None, ai_suggestion=None)
        value.update(changes)
        return value

    def test_author_evidence(self):
        method = dict(method="关闭提醒", evidence="关闭提醒", conditions="处理需要专注的任务")
        result = validate_association(self.result(author_method=method), "作者建议关闭提醒。")
        self.assertEqual(result.author_method.evidence, "关闭提醒")
        with self.assertRaises(ValueError):
            validate_association(self.result(author_method=method), "没有该方法")

    def test_labels_and_abstention(self):
        self.assertIsNone(validate_association(self.result(sufficient=False), "原文").ai_suggestion)
        self.assertEqual(validate_association(self.result(ai_suggestion="试一次"), "原文").ai_suggestion, "试一次")
        with self.assertRaises(ValueError):
            validate_association(self.result(sufficient=False, ai_suggestion="强行行动"), "原文")

    def test_endpoint_and_failure(self):
        with patch('generation.associate', return_value=self.result()) as model:
            association(AssociationRequest(problem="当前问题", context="已确认片段"))
            model.assert_called_once_with("当前问题", "已确认片段")
        with self.assertRaises(HTTPException) as empty:
            association(AssociationRequest(problem=" ", context="原文"))
        self.assertEqual(empty.exception.status_code, 400)
        with patch('generation.associate', side_effect=RuntimeError("private diagnostic")):
            with self.assertRaises(HTTPException) as failure:
                association(AssociationRequest(problem="问题", context="原文"))
            self.assertNotIn("private", failure.exception.detail)


if __name__ == '__main__':
    unittest.main()
