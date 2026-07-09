ALL_ROLES = [
    "IT_ADMIN",
    "LECTURER",
    "LAB_COORDINATOR",
    "ADMINISTRATION",
    "STUDENT",
]


SIDEBAR_ITEMS = [
    {
        "label": "Dashboard",
        "url_name": "core:dashboard",
        "href": None,
        "match": "/dashboard/",
        "roles": ALL_ROLES,
    },
    {
        "label": "Accounts Dashboard",
        "url_name": "accounts:dashboard",
        "href": None,
        "match": "/accounts/manage/",
        "roles": ["IT_ADMIN"],
    },
    {
        "label": "Academic Setup",
        "url_name": "academics:dashboard",
        "href": None,
        "match": "/academics/",
        "roles": ["IT_ADMIN", "ADMINISTRATION"],
    },
    {
        "label": "Lab Bookings",
        "url_name": "bookings:dashboard",
        "href": None,
        "match": "/bookings/",
        "roles": ["LECTURER", "LAB_COORDINATOR", "ADMINISTRATION"],
    },
    {
        "label": "Skills Lab",
        "url_name": "labs:dashboard",
        "href": None,
        "match": "/labs/",
        "roles": ["LAB_COORDINATOR", "ADMINISTRATION", "IT_ADMIN"],
    },
    {
        "label": "Data Imports",
        "url_name": "bulk_imports:batch_list",
        "href": None,
        "match": "/imports/",
        "roles": ["IT_ADMIN", "ADMINISTRATION"],
    },
    {
        "label": "Attendance",
        "url_name": None,
        "href": "#",
        "match": "/attendance/",
        "roles": ["LECTURER", "ADMINISTRATION", "STUDENT"],
    },
    {
        "label": "Self-Practice",
        "url_name": None,
        "href": "#",
        "match": "/labs/self-practice/",
        "roles": ["STUDENT", "LECTURER", "LAB_COORDINATOR"],
    },
    {
        "label": "OSCE Assessments",
        "url_name": None,
        "href": "#",
        "match": "/assessments/",
        "roles": ["LECTURER", "ADMINISTRATION", "STUDENT"],
    },
    {
        "label": "Inventory",
        "url_name": None,
        "href": "#",
        "match": "/inventory/",
        "roles": ["LECTURER", "LAB_COORDINATOR", "ADMINISTRATION"],
    },
    {
        "label": "Clinical Reports",
        "url_name": None,
        "href": "#",
        "match": "/reports/",
        "roles": ["LECTURER", "ADMINISTRATION", "STUDENT"],
    },
    {
        "label": "Users & Permissions",
        "url_name": "accounts:user_list",
        "href": None,
        "match": "/accounts/manage/",
        "roles": ["IT_ADMIN"],
    },
    {
        "label": "Notifications",
        "url_name": None,
        "href": "#",
        "match": "/notifications/",
        "roles": ALL_ROLES,
    },
]


DASHBOARD_CARDS = {
    "IT_ADMIN": [
        {
            "title": "Users",
            "value": "Manage",
            "description": "Create accounts, reset passwords, and manage permissions.",
            "href": "#",
        },
        {
            "title": "Audit Logs",
            "value": "Monitor",
            "description": "Track sensitive updates to attendance, marks, and inventory.",
            "href": "#",
        },
        {
            "title": "System Settings",
            "value": "Configure",
            "description": "Manage rules, roles, and platform configuration.",
            "href": "#",
        },
        {
            "title": "Academic Setup",
            "value": "Manage",
            "description": "Manage programs, cohorts, academic years, semesters, and modules.",
            "href": "/academics/",
        }
    ],
    "LECTURER": [
        {
            "title": "Demonstrations",
            "value": "Book",
            "description": "Request demonstrations and record attendance.",
            "href": "#",
        },
        {
            "title": "Self-Practice",
            "value": "Supervise",
            "description": "Verify student practice and procedures performed.",
            "href": "#",
        },
        {
            "title": "OSCE Marks",
            "value": "Enter",
            "description": "Record OSCE station scores and export marks.",
            "href": "#",
        },
    ],
    "LAB_COORDINATOR": [
        {
            "title": "Booking Requests",
            "value": "Approve",
            "description": "Approve or reject lab bookings.",
            "href": "#",
        },
        {
            "title": "Lab Schedule",
            "value": "Plan",
            "description": "Monitor room usage and upcoming sessions.",
            "href": "#",
        },
        {
            "title": "Inventory Usage",
            "value": "Review",
            "description": "Approve usage and monitor consumables.",
            "href": "#",
        },
    ],
    "ADMINISTRATION": [
        {
            "title": "Student Monitoring",
            "value": "Track",
            "description": "Monitor attendance, eligibility, and progression.",
            "href": "#",
        },
        {
            "title": "OSCE Approval",
            "value": "Approve",
            "description": "Approve final OSCE marks before publication.",
            "href": "#",
        },
        {
            "title": "Reports",
            "value": "Export",
            "description": "Download marks, attendance, and clinical reports.",
            "href": "#",
        },
    ],
    "STUDENT": [
        {
            "title": "Attendance",
            "value": "80%",
            "description": "Track demonstration attendance and eligibility.",
            "href": "#",
        },
        {
            "title": "Self-Practice",
            "value": "Book",
            "description": "Request practice sessions after eligibility is met.",
            "href": "#",
        },
        {
            "title": "OSCE Results",
            "value": "View",
            "description": "View published OSCE marks and retake status.",
            "href": "#",
        },
    ],
}


def get_user_role(user):
    if not user or not user.is_authenticated:
        return None

    return getattr(user, "role", None)


def get_sidebar_items(user):
    role = get_user_role(user)

    if role is None:
        return []

    return [
        item
        for item in SIDEBAR_ITEMS
        if role in item["roles"]
    ]


def get_dashboard_cards(user):
    role = get_user_role(user)

    return DASHBOARD_CARDS.get(role, [])