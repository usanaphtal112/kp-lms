from django.urls import path

from .views import (
    AcademicDashboardView,
    AcademicYearCreateView,
    AcademicYearListView,
    AcademicYearUpdateView,
    ApproveCreditTransferView,
    CohortCreateView,
    CohortListView,
    CohortUpdateView,
    CreditTransferCreateView,
    CreditTransferListView,
    CreditTransferUpdateView,
    DepartmentCreateView,
    DepartmentListView,
    DepartmentUpdateView,
    EnrollCohortStudentsView,
    FacultyCreateView,
    FacultyListView,
    FacultyUpdateView,
    ModuleCreateView,
    ModuleDetailView,
    ModuleEnrollmentCreateView,
    ModuleEnrollmentListView,
    ModuleEnrollmentUpdateView,
    ModuleListView,
    ModuleOfferingCreateView,
    ModuleOfferingDetailView,
    ModuleOfferingListView,
    ModuleOfferingUpdateView,
    ModuleUpdateView,
    ProcedureCreateView,
    ProcedureListView,
    ProcedureRequirementCreateView,
    ProcedureRequirementListView,
    ProcedureRequirementUpdateView,
    ProcedureUpdateView,
    ProgramCreateView,
    ProgramListView,
    ProgramUpdateView,
    RejectCreditTransferView,
    SemesterCreateView,
    SemesterListView,
    SemesterUpdateView,
    SetCurrentAcademicYearView,
    SetCurrentSemesterView,
)


app_name = "academics"

urlpatterns = [
    path("", AcademicDashboardView.as_view(), name="dashboard"),

    path("faculties/", FacultyListView.as_view(), name="faculty_list"),
    path("faculties/create/", FacultyCreateView.as_view(), name="faculty_create"),
    path("faculties/<int:pk>/update/", FacultyUpdateView.as_view(), name="faculty_update"),

    path("departments/", DepartmentListView.as_view(), name="department_list"),
    path("departments/create/", DepartmentCreateView.as_view(), name="department_create"),
    path("departments/<int:pk>/update/", DepartmentUpdateView.as_view(), name="department_update"),

    path("programs/", ProgramListView.as_view(), name="program_list"),
    path("programs/create/", ProgramCreateView.as_view(), name="program_create"),
    path("programs/<int:pk>/update/", ProgramUpdateView.as_view(), name="program_update"),

    path("cohorts/", CohortListView.as_view(), name="cohort_list"),
    path("cohorts/create/", CohortCreateView.as_view(), name="cohort_create"),
    path("cohorts/<int:pk>/update/", CohortUpdateView.as_view(), name="cohort_update"),

    path("academic-years/", AcademicYearListView.as_view(), name="academic_year_list"),
    path("academic-years/create/", AcademicYearCreateView.as_view(), name="academic_year_create"),
    path("academic-years/<int:pk>/update/", AcademicYearUpdateView.as_view(), name="academic_year_update"),
    path("academic-years/<int:pk>/set-current/", SetCurrentAcademicYearView.as_view(), name="academic_year_set_current"),

    path("semesters/", SemesterListView.as_view(), name="semester_list"),
    path("semesters/create/", SemesterCreateView.as_view(), name="semester_create"),
    path("semesters/<int:pk>/update/", SemesterUpdateView.as_view(), name="semester_update"),
    path("semesters/<int:pk>/set-current/", SetCurrentSemesterView.as_view(), name="semester_set_current"),

    path("modules/", ModuleListView.as_view(), name="module_list"),
    path("modules/create/", ModuleCreateView.as_view(), name="module_create"),
    path("modules/<int:pk>/", ModuleDetailView.as_view(), name="module_detail"),
    path("modules/<int:pk>/update/", ModuleUpdateView.as_view(), name="module_update"),

    path("offerings/", ModuleOfferingListView.as_view(), name="offering_list"),
    path("offerings/create/", ModuleOfferingCreateView.as_view(), name="offering_create"),
    path("offerings/<int:pk>/", ModuleOfferingDetailView.as_view(), name="offering_detail"),
    path("offerings/<int:pk>/update/", ModuleOfferingUpdateView.as_view(), name="offering_update"),
    path("offerings/<int:pk>/enroll-cohort/", EnrollCohortStudentsView.as_view(), name="offering_enroll_cohort"),

    path("procedures/", ProcedureListView.as_view(), name="procedure_list"),
    path("procedures/create/", ProcedureCreateView.as_view(), name="procedure_create"),
    path("procedures/<int:pk>/update/", ProcedureUpdateView.as_view(), name="procedure_update"),

    path("procedure-requirements/", ProcedureRequirementListView.as_view(), name="procedure_requirement_list"),
    path("procedure-requirements/create/", ProcedureRequirementCreateView.as_view(), name="procedure_requirement_create"),
    path("procedure-requirements/<int:pk>/update/", ProcedureRequirementUpdateView.as_view(), name="procedure_requirement_update"),

    path("enrollments/", ModuleEnrollmentListView.as_view(), name="enrollment_list"),
    path("enrollments/create/", ModuleEnrollmentCreateView.as_view(), name="enrollment_create"),
    path("enrollments/<int:pk>/update/", ModuleEnrollmentUpdateView.as_view(), name="enrollment_update"),

    path("credit-transfers/", CreditTransferListView.as_view(), name="credit_transfer_list"),
    path("credit-transfers/create/", CreditTransferCreateView.as_view(), name="credit_transfer_create"),
    path("credit-transfers/<int:pk>/update/", CreditTransferUpdateView.as_view(), name="credit_transfer_update"),
    path("credit-transfers/<int:pk>/approve/", ApproveCreditTransferView.as_view(), name="credit_transfer_approve"),
    path("credit-transfers/<int:pk>/reject/", RejectCreditTransferView.as_view(), name="credit_transfer_reject"),
]