"""Static business vocabulary values the app validates against but doesn't store as rows."""

SURVEY_TYPES: tuple[str, ...] = (
    "Nat Rep/Gen-Pop",
    "Complex surveys",
    "Nat Rep multi-country",
    "B2B",
    "Multicountry B2B",
    "Multi-country",
    "Regional",
    "Demographic-Specific",
    "Occupational/Interest/Behavioral niche groups",
    "Internal Surveys",
)

SUB_STATUSES: dict[str, tuple[str, ...]] = {
    "CLIENT_REVIEW": ("AWAITING_CLIENT", "CHANGES_REQUESTED"),
    "LIVE": ("SOFT_LAUNCH", "FULL_LAUNCH"),
}

ALL_SUB_STATUSES: frozenset[str] = frozenset(
    status for statuses in SUB_STATUSES.values() for status in statuses
)

# Checklists are hardcoded per stage (ADR 0002). Every item carries a stable id, so the
# stored tick survives a reworded label. Source: "3Gem Scripter Self-Check".
# The paper form has two boxes per row — done, or not applicable — so state is tri-state.
CHECKLIST_STATES: tuple[str, ...] = ("done", "na")

# QA repeats the scripter's own checks before the link goes out — the second pair of
# eyes is the point, so the items are shared rather than paraphrased.
_SCRIPTING_SECTIONS: tuple[dict, ...] = (
    {
        "section": "Project setup",
        "items": (
            ("latest_questionnaire", "Latest questionnaire and all client amendments implemented"),
        ),
    },
    {
        "section": "Programming",
        "items": (
            ("routing_skip_logic", "Routing and skip logic tested"),
            ("display_logic", "Display / show-hide logic verified"),
            ("mandatory_optional", "Mandatory and optional questions verified"),
            ("validation_rules", "Validation rules tested"),
            ("piping", "Piping verified"),
            ("loops_grids", "Loops and grids tested"),
            ("randomisation", "Randomisation / rotation verified"),
            ("variable_naming", "Variable naming follows project standards"),
        ),
    },
    {
        "section": "Testing",
        "items": (
            ("estimated_loi", "Estimated LOI acceptable"),
            ("test_link", "Test link verified"),
        ),
    },
)

CHECKLISTS: dict[str, tuple[dict, ...]] = {
    "scripting": _SCRIPTING_SECTIONS,
    "qa": _SCRIPTING_SECTIONS
    + (
        {
            "section": "QA testing",
            "items": (
                ("complete_interview", "Complete interview tested"),
                ("screenout_routes", "Screenout routes tested"),
                ("desktop_tested", "Desktop tested"),
                ("mobile_tested", "Mobile tested"),
            ),
        },
        {
            # Derived, never set by hand: it ticks itself when everything above is answered.
            "section": "Sign-off",
            "derived": True,
            "items": (("qa_signed_off", "QA complete — ready for the client"),),
        },
    ),
}

CHECKLIST_COLUMNS: dict[str, str] = {
    "scripting": "scripting_checklist_state",
    "qa": "qa_checklist_state",
    "quota": "quota_checklist_state",
    "final_qa": "final_qa_checklist_state",
}

CHECKLIST_ITEM_IDS: dict[str, frozenset[str]] = {
    name: frozenset(item_id for section in sections for item_id, _ in section["items"])
    for name, sections in CHECKLISTS.items()
}

# Items the app ticks on the user's behalf — rejected if sent in a PATCH.
DERIVED_ITEM_IDS: dict[str, frozenset[str]] = {
    name: frozenset(
        item_id
        for section in sections
        if section.get("derived")
        for item_id, _ in section["items"]
    )
    for name, sections in CHECKLISTS.items()
}

# What a person actually has to answer before a gate opens.
REQUIRED_ITEM_IDS: dict[str, frozenset[str]] = {
    name: ids - DERIVED_ITEM_IDS[name] for name, ids in CHECKLIST_ITEM_IDS.items()
}