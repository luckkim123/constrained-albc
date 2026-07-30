"""Architecture-specific export specs, keyed by name in SPEC_REGISTRY."""
from constrained_albc.deploy.specs.student_gru import StudentGRUSpec
from constrained_albc.deploy.specs.student_tcn import StudentTCNSpec
from constrained_albc.deploy.specs.teacher_actor import TeacherActorSpec

SPEC_REGISTRY = {
    StudentGRUSpec.name: StudentGRUSpec,
    StudentTCNSpec.name: StudentTCNSpec,
    TeacherActorSpec.name: TeacherActorSpec,
}

# encoder_type as recorded in the student checkpoint's cfg -> its export spec.
# The checkpoint declares its own architecture; the exporter never guesses.
STUDENT_SPEC_BY_ENCODER = {
    "tcn": StudentTCNSpec,
    "gru": StudentGRUSpec,
}

__all__ = ["SPEC_REGISTRY", "STUDENT_SPEC_BY_ENCODER",
           "StudentGRUSpec", "StudentTCNSpec", "TeacherActorSpec"]
