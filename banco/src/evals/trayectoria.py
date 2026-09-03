from pydantic import BaseModel

class ExpectedTrajectory(BaseModel):
    must_include: list[str]
    must_not_include: list[str]
    order: list[tuple[str, str]] = []

EXPECTED = ExpectedTrajectory(
    must_include=[
        "verificar_identidad", "bloquear_tarjeta_dry_run", "interrupt",
    ],
    must_not_include=["bloquear_tarjeta_commit"],
    order=[("bloquear_tarjeta_dry_run", "interrupt")],
)

def assert_trajectory(trace, expected):
    names = [span.name for span in trace.spans]
    for name in expected.must_include:
        assert name in names
    for name in expected.must_not_include:
        assert name not in names
    for before, after in expected.order:
        assert names.index(before) < names.index(after)
