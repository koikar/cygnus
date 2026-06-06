"""End-to-end antifragility demo, in simulation, with no hardware or API keys.

Runs a sequence of episodes where the cube is sometimes placed in a novel zone
(a black swan for the blind habit). The first time a swan appears the system
escalates to System-2 and learns; every repeat is then a fast System-1 recall.
The printed table and curve show escalations — and total cost — falling: the
robot getting *stronger* from rare failures.

    python -m reflexos demo
"""

from __future__ import annotations

from .cognition import build_cognition
from .controller import Controller, EpisodeResult
from .detector import BlackSwanDetector
from .robot import SimBackend

# zone "A" is the habit; B and C are black swans the first time they appear.
DEFAULT_SCENARIO = ["A", "B", "B", "C", "C", "B"]


def run(scenario: list[str] | None = None) -> list[EpisodeResult]:
    scenario = scenario or DEFAULT_SCENARIO
    robot = SimBackend()
    robot.connect()
    cognition = build_cognition("local")  # offline: SQLite + scripted reasoner
    controller = Controller(robot, cognition, BlackSwanDetector())

    results: list[EpisodeResult] = []
    for i, zone in enumerate(scenario, start=1):
        robot.reset(cube_zone=zone)
        results.append(controller.run_episode(i))
    robot.disconnect()
    return results


def _bar(total_calls: int) -> str:
    return "█" * total_calls


def render(results: list[EpisodeResult]) -> str:
    lines: list[str] = []
    lines.append("ReflexOS — antifragility demo (simulated SO-101)\n")
    header = f"{'ep':>2}  {'cube':<5} {'mode':<7} {'swan':<5} {'ok':<3} {'cost':>4}  cost"
    lines.append(header)
    lines.append("-" * len(header))
    for r in results:
        cost = r.tool_calls + r.recovery_calls
        lines.append(
            f"{r.episode:>2}  "
            f"{str(r.cube_zone):<5} "
            f"{r.mode:<7} "
            f"{('YES' if r.escalated else '·'):<5} "
            f"{('✓' if r.success else '✗'):<3} "
            f"{cost:>4}  {_bar(cost)}"
        )

    escalations = sum(1 for r in results if r.escalated)
    learned = {r.signature for r in results if r.escalated and r.success}
    lines.append("")
    lines.append(
        f"episodes={len(results)}  escalations={escalations}  "
        f"reflexes_learned={len(learned)}  "
        f"all_succeeded={all(r.success for r in results)}"
    )
    lines.append(
        "Read the curve: a novel zone escalates once (high cost), then every "
        "repeat is a cheap reflex — recovery cost bends down toward the habit."
    )
    return "\n".join(lines)


def main() -> None:
    print(render(run()))


if __name__ == "__main__":
    main()
