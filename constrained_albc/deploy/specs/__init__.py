"""Architecture-specific export specs, keyed by name in SPEC_REGISTRY."""
from constrained_albc.deploy.specs.student_tcn import StudentTCNSpec
from constrained_albc.deploy.specs.teacher_actor import TeacherActorSpec

SPEC_REGISTRY = {
    StudentTCNSpec.name: StudentTCNSpec,
    TeacherActorSpec.name: TeacherActorSpec,
}

__all__ = ["SPEC_REGISTRY", "StudentTCNSpec", "TeacherActorSpec"]
