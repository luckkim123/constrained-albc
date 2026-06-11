"""STUB — replaced in Task 4 with the real filter+rename implementation."""
from __future__ import annotations

from constrained_albc.deploy.spec import ExportSpec


class TeacherActorSpec(ExportSpec):
    name = "teacher_actor"
    npz_filename = "weights_teacher.npz"
    key_contract = {}

    def build_model(self, ckpt, device):
        raise NotImplementedError

    def map_state_dict(self, model):
        raise NotImplementedError
