from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


DAYS: Tuple[str, ...] = ("Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma")
MAX_HOURS_PER_DAY = 6


@dataclass(frozen=True)
class ScheduleConfig:
    days: Sequence[str] = DAYS
    max_hours_per_day: int = MAX_HOURS_PER_DAY

    @property
    def capacity(self) -> int:
        return len(self.days) * self.max_hours_per_day


class ScheduleGenerator:
    def __init__(self, subjects: Dict[str, int], config: Optional[ScheduleConfig] = None):
        self.subjects = {name.strip(): int(hours) for name, hours in subjects.items() if name.strip() and int(hours) > 0}
        if not self.subjects:
            raise ValueError("Hech qanday fanlar topilmadi.")

        total_hours = sum(self.subjects.values())
        if config is None and total_hours > ScheduleConfig().capacity:
            required_days = max(1, math.ceil(total_hours / ScheduleConfig().max_hours_per_day))
            self.config = ScheduleConfig(days=tuple(f"Kun {idx}" for idx in range(1, required_days + 1)))
        else:
            self.config = config or ScheduleConfig()

        if config is None and sum(self.subjects.values()) > self.config.capacity:
            extra_days = max(1, math.ceil(sum(self.subjects.values()) / self.config.max_hours_per_day))
            self.config = ScheduleConfig(
                days=tuple(f"Kun {idx}" for idx in range(1, extra_days + 1)),
                max_hours_per_day=self.config.max_hours_per_day,
            )

        self._validate_capacity()

    def _validate_capacity(self) -> None:
        if sum(self.subjects.values()) > self.config.capacity:
            raise ValueError("Jami soatlar haftalik sig'imdan oshib ketdi (5 kun x 6 soat).")

    @staticmethod
    def is_priority_subject(subject: str) -> bool:
        lowered = subject.lower()
        return "matematika" in lowered or "ingliz tili" in lowered

    def generate(
        self,
        exclude_signatures: Optional[Set[str]] = None,
        max_attempts: int = 400,
        random_seed: Optional[int] = None,
        blocked_teacher_slots: Optional[Set[Tuple[str, int, int]]] = None,
    ) -> List[List[Optional[str]]]:
        excludes = exclude_signatures or set()
        rng = random.Random(random_seed)

        for _ in range(max_attempts):
            schedule = [[None for _ in range(self.config.max_hours_per_day)] for _ in self.config.days]
            day_load = [0 for _ in self.config.days]

            priority_subjects = [name for name in self.subjects if self.is_priority_subject(name)]
            rng.shuffle(priority_subjects)

            remaining_hours: Dict[str, int] = {}
            for subject in priority_subjects:
                pair_count = self.subjects[subject] // 2
                for _ in range(pair_count):
                    placed = self._place_priority_pair(schedule, day_load, subject, rng, blocked_teacher_slots)
                    if not placed:
                        break
                remaining_hours[subject] = self.subjects[subject] - self._count_subject(schedule, subject)

            single_slots: List[str] = []
            for subject, hours in self.subjects.items():
                already_placed = self._count_subject(schedule, subject)
                needed = max(0, hours - already_placed)
                single_slots.extend([subject] * needed)
            rng.shuffle(single_slots)

            ok = True
            for subject in single_slots:
                if not self._place_single(schedule, day_load, subject, rng, blocked_teacher_slots):
                    ok = False
                    break
            if not ok:
                continue

            signature = self.schedule_signature(schedule)
            if signature not in excludes:
                return schedule

        raise ValueError("Yangi jadval varianti topilmadi. Soatlarni kamaytirib qayta urinib ko'ring.")

    def _place_priority_pair(
        self,
        schedule: List[List[Optional[str]]],
        day_load: List[int],
        subject: str,
        rng: random.Random,
        blocked_teacher_slots: Optional[Set[Tuple[str, int, int]]] = None,
    ) -> bool:
        day_indexes = list(range(len(self.config.days)))
        rng.shuffle(day_indexes)

        candidates: List[Tuple[float, int, int]] = []
        for day_idx in day_indexes:
            for hour_idx in range(self.config.max_hours_per_day - 1):
                teacher = subject.rsplit("\n", 1)[-1]
                slots_available = (
                    not blocked_teacher_slots
                    or (
                        (teacher, day_idx, hour_idx) not in blocked_teacher_slots
                        and (teacher, day_idx, hour_idx + 1) not in blocked_teacher_slots
                    )
                )
                if (
                    schedule[day_idx][hour_idx] is None
                    and schedule[day_idx][hour_idx + 1] is None
                    and slots_available
                ):
                    score = hour_idx * 10 + day_load[day_idx] * 2 + rng.random()
                    candidates.append((score, day_idx, hour_idx))

        if not candidates:
            return False

        _, day_idx, hour_idx = min(candidates, key=lambda item: item[0])
        schedule[day_idx][hour_idx] = subject
        schedule[day_idx][hour_idx + 1] = subject
        day_load[day_idx] += 2
        return True

    def _place_single(
        self,
        schedule: List[List[Optional[str]]],
        day_load: List[int],
        subject: str,
        rng: random.Random,
        blocked_teacher_slots: Optional[Set[Tuple[str, int, int]]] = None,
    ) -> bool:
        priority = self.is_priority_subject(subject)
        candidates: List[Tuple[float, int, int]] = []

        for day_idx in range(len(self.config.days)):
            for hour_idx in range(self.config.max_hours_per_day):
                teacher = subject.rsplit("\n", 1)[-1]
                if schedule[day_idx][hour_idx] is None and (
                    not blocked_teacher_slots
                    or (teacher, day_idx, hour_idx) not in blocked_teacher_slots
                ):
                    if priority:
                        score = hour_idx * 8 + day_load[day_idx] * 2 + rng.random()
                    else:
                        score = day_load[day_idx] * 2 + hour_idx + rng.random()
                    candidates.append((score, day_idx, hour_idx))

        if not candidates:
            return False

        _, day_idx, hour_idx = min(candidates, key=lambda item: item[0])
        schedule[day_idx][hour_idx] = subject
        day_load[day_idx] += 1
        return True

    @staticmethod
    def _count_subject(schedule: List[List[Optional[str]]], subject: str) -> int:
        return sum(1 for day in schedule for value in day if value == subject)

    @staticmethod
    def schedule_signature(schedule: List[List[Optional[str]]]) -> str:
        return "|".join(",".join(slot or "-" for slot in day) for day in schedule)

    def to_hour_major(self, schedule: List[List[Optional[str]]]) -> List[List[str]]:
        rows: List[List[str]] = []
        for hour_idx in range(self.config.max_hours_per_day):
            row = []
            for day_idx in range(len(self.config.days)):
                row.append(schedule[day_idx][hour_idx] or "")
            rows.append(row)
        return rows


def generate_class_schedules(
    class_subjects: Dict[str, Dict[str, int]],
    config: Optional[ScheduleConfig] = None,
    exclude_signatures: Optional[Set[str]] = None,
    max_attempts: int = 400,
) -> Dict[str, List[List[Optional[str]]]]:
    """Generate class schedules while preventing a teacher's parallel lessons."""
    schedule_config = config or ScheduleConfig()
    rng = random.Random()
    excludes = exclude_signatures or set()

    for _ in range(max_attempts):
        schedules: Dict[str, List[List[Optional[str]]]] = {}
        occupied_teachers: Set[Tuple[str, int, int]] = set()
        ordered_classes = sorted(class_subjects.items(), key=lambda item: sum(item[1].values()), reverse=True)
        for class_name, subjects in ordered_classes:
            generator = ScheduleGenerator(subjects, config=schedule_config)
            schedule = generator.generate(
                random_seed=rng.randrange(1_000_000_000),
                blocked_teacher_slots=occupied_teachers,
            )
            schedules[class_name] = schedule
            for day_index, day in enumerate(schedule):
                for period_index, lesson in enumerate(day):
                    if lesson:
                        teacher = lesson.rsplit("\n", 1)[-1]
                        occupied_teachers.add((teacher, day_index, period_index))

        signature = "|".join(
            f"{class_name}:{ScheduleGenerator.schedule_signature(schedule)}"
            for class_name, schedule in sorted(schedules.items())
        )
        if signature not in excludes:
            return schedules

    raise ValueError(
        "O'qituvchilar to'qnashuvsiz yangi jadval topilmadi. "
        "O'qituvchilarning jami dars soatlarini tekshiring."
    )
