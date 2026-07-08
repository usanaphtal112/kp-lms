from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.academics.models import (
    AcademicYear,
    Cohort,
    Department,
    Faculty,
    Module,
    Program,
    Semester,
)


class Command(BaseCommand):
    help = "Seed initial KP-HSLMS academic structure."

    def handle(self, *args, **options):
        faculty, _ = Faculty.objects.get_or_create(
            code="FHS",
            defaults={
                "name": "Faculty of Health Sciences",
            },
        )

        department, _ = Department.objects.get_or_create(
            faculty=faculty,
            code="NUR",
            defaults={
                "name": "Department of Nursing",
            },
        )

        program, _ = Program.objects.get_or_create(
            department=department,
            code="BNS",
            defaults={
                "name": "Bachelor of Nursing Sciences",
                "award_type": "BACHELOR",
                "duration_years": 4,
            },
        )

        current_year = timezone.localdate().year

        cohort, _ = Cohort.objects.get_or_create(
            program=program,
            code=f"BNS-{current_year}",
            defaults={
                "name": f"BNS Intake {current_year}",
                "intake_year": current_year,
                "graduation_year": current_year + 4,
                "status": "ACTIVE",
            },
        )

        academic_year, _ = AcademicYear.objects.get_or_create(
            name=f"{current_year}/{current_year + 1}",
            defaults={
                "start_date": f"{current_year}-09-01",
                "end_date": f"{current_year + 1}-08-31",
                "is_current": True,
            },
        )

        Semester.objects.get_or_create(
            academic_year=academic_year,
            semester_number=1,
            defaults={
                "name": "Semester I",
                "start_date": f"{current_year}-09-01",
                "end_date": f"{current_year + 1}-01-31",
                "is_current": True,
            },
        )

        Module.objects.get_or_create(
            program=program,
            code="FON101",
            defaults={
                "title": "Fundamentals of Nursing I",
                "year_level": 1,
                "semester_number": 1,
                "credits": 12,
                "attendance_requirement": "80.00",
                "pass_mark": "60.00",
            },
        )

        Module.objects.get_or_create(
            program=program,
            code="FON102",
            defaults={
                "title": "Fundamentals of Nursing II",
                "year_level": 1,
                "semester_number": 2,
                "credits": 12,
                "attendance_requirement": "80.00",
                "pass_mark": "60.00",
            },
        )

        self.stdout.write(self.style.SUCCESS("Academic seed data created."))