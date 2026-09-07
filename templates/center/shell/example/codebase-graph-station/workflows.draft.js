// DRAFT user workflows — machine-proposed by `/gabe-cc-update curate-workflows` (draft-workflows.py)
// from the committed c4-graph (head 8356f531): every endpoint no curated workflow names, clustered by
// entity · the screen that drives it, steps ordered read→write, NAMED in the user's words (what the person
// does — the legend reference's definitions logic) and LEVELED into its tier (Orientation · Core ·
// Specialized), so each draft already sits in its section of the workflows tab wearing the DRAFT chip.
// Accept one by moving its entry into workflows.js (rename freely) — the next run drops it.
// Regenerated wholesale; never hand-edit. Absent or empty → the station shows no drafts.
window.GABE_WORKFLOWS_DRAFT = [
  {
    "name": "Look at cooking sessions — photos",
    "level": 1,
    "draft": true,
    "note": "look at cooking sessions from the CookingFlowContainer screen — the app reads CookingPhoto, CookingSession; 1 endpoint, no writes → Orientation (level 1). A DRAFT: accept it by moving this entry into workflows.js (rename freely).",
    "steps": [
      "GET /cooking/sessions/{session_id}/photos/{slot}"
    ],
    "cluster": {
      "entity": "cooking",
      "screen": "CookingFlowContainer"
    },
    "why": {
      "writes": 0,
      "reads": 2,
      "span": [
        "cooking"
      ]
    }
  },
  {
    "name": "Manage cooking — active · reminders · due · dishes · …",
    "level": 3,
    "draft": true,
    "note": "manage cooking from the CookingRoute screen — the app reads CookingPhoto, CookingSession, CookingStageReminder, CookingStepProgress… and writes CookingPhoto, CookingSession, Notification; 7 endpoints, cross-entity writes → Specialized (level 3). A DRAFT: accept it by moving this entry into workflows.js (rename freely).",
    "steps": [
      "GET /cooking/active",
      "GET /cooking/reminders/due",
      "GET /history/dishes",
      "GET /notifications",
      "POST /cooking/sessions/{session_id}/cancel",
      "PATCH /cooking/sessions/{session_id}/readiness",
      "DELETE /cooking/sessions/{session_id}/photos/{slot}"
    ],
    "cluster": {
      "entity": "cooking",
      "screen": "CookingRoute"
    },
    "why": {
      "writes": 3,
      "reads": 7,
      "span": [
        "cooking",
        "recipe"
      ]
    }
  },
  {
    "name": "Look at consent",
    "level": 1,
    "draft": true,
    "note": "look at consent from the SetupRoute screen — the app reads ConsentRecord; 1 endpoint, no writes → Orientation (level 1). A DRAFT: accept it by moving this entry into workflows.js (rename freely).",
    "steps": [
      "GET /consent"
    ],
    "cluster": {
      "entity": "legal-consent",
      "screen": "SetupRoute"
    },
    "why": {
      "writes": 0,
      "reads": 1,
      "span": [
        "legal-consent"
      ]
    }
  },
  {
    "name": "Look at pantry locations",
    "level": 1,
    "draft": true,
    "note": "look at pantry locations from the CookingRoute screen — the app reads Location; 1 endpoint, no writes → Orientation (level 1). A DRAFT: accept it by moving this entry into workflows.js (rename freely).",
    "steps": [
      "GET /pantry/locations"
    ],
    "cluster": {
      "entity": "pantry",
      "screen": "CookingRoute"
    },
    "why": {
      "writes": 0,
      "reads": 1,
      "span": [
        "pantry"
      ]
    }
  },
  {
    "name": "Look at pantry — history",
    "level": 1,
    "draft": true,
    "note": "look at pantry from the IngredientHistoryRoute screen — the app reads IngredientHistoryEvent; 1 endpoint, no writes → Orientation (level 1). A DRAFT: accept it by moving this entry into workflows.js (rename freely).",
    "steps": [
      "GET /pantry/history"
    ],
    "cluster": {
      "entity": "pantry",
      "screen": "IngredientHistoryRoute"
    },
    "why": {
      "writes": 0,
      "reads": 1,
      "span": [
        "pantry"
      ]
    }
  },
  {
    "name": "Add pantry — frequent ingredients · reset · apply · preview · …",
    "level": 3,
    "draft": true,
    "note": "add pantry from the PantryRoute screen — the app reads CanonicalIngredient, IngredientAlias, IngredientHistoryEvent, PantryItem… and writes IngredientHistoryEvent, PantryItem, PantryResetDecision, PantryResetOperation; 4 endpoints, cross-entity writes → Specialized (level 3). A DRAFT: accept it by moving this entry into workflows.js (rename freely).",
    "steps": [
      "GET /pantry/frequent-ingredients",
      "POST /pantry/reset/apply",
      "POST /pantry/reset/preview",
      "POST /pantry/resolve-batch"
    ],
    "cluster": {
      "entity": "pantry",
      "screen": "PantryRoute"
    },
    "why": {
      "writes": 4,
      "reads": 6,
      "span": [
        "pantry",
        "recipe"
      ]
    }
  },
  {
    "name": "Add shopping items — add to list",
    "level": 3,
    "draft": true,
    "note": "add shopping items from the ShoppingRoute screen — the app reads IngredientHistoryEvent, PlannedRecipe, RecipeIngredient, ShoppingItem and writes ShoppingItem; 1 endpoint, cross-entity writes → Specialized (level 3). A DRAFT: accept it by moving this entry into workflows.js (rename freely).",
    "steps": [
      "POST /shopping/items/{source_id}/add-to-list"
    ],
    "cluster": {
      "entity": "pantry",
      "screen": "ShoppingRoute"
    },
    "why": {
      "writes": 1,
      "reads": 4,
      "span": [
        "pantry",
        "recipe"
      ]
    }
  },
  {
    "name": "Look at profile — summary",
    "level": 1,
    "draft": true,
    "note": "look at profile from the HomeRoute screen — the app reads DishHistoryEvent, NodeProgress, Recipe, SkillTree…; 1 endpoint, no writes → Orientation (level 1). A DRAFT: accept it by moving this entry into workflows.js (rename freely).",
    "steps": [
      "GET /profile/summary"
    ],
    "cluster": {
      "entity": "progression",
      "screen": "HomeRoute"
    },
    "why": {
      "writes": 0,
      "reads": 7,
      "span": [
        "allergen",
        "auth",
        "cooking",
        "progression",
        "recipe"
      ]
    }
  },
  {
    "name": "Look at equipment",
    "level": 1,
    "draft": true,
    "note": "look at equipment from the CookingRoute screen — the app reads UserEquipment; 1 endpoint, no writes → Orientation (level 1). A DRAFT: accept it by moving this entry into workflows.js (rename freely).",
    "steps": [
      "GET /equipment"
    ],
    "cluster": {
      "entity": "recipe",
      "screen": "CookingRoute"
    },
    "why": {
      "writes": 0,
      "reads": 1,
      "span": [
        "recipe"
      ]
    }
  },
  {
    "name": "Edit settings — household · preferences",
    "level": 1,
    "draft": true,
    "note": "edit settings from the SetupRoute screen — the app reads HouseholdFormatPreferences, SubscriptionEntitlement, UserDietaryProfile, UserExplorationPreferences…; 2 endpoints, no writes → Orientation (level 1). A DRAFT: accept it by moving this entry into workflows.js (rename freely).",
    "steps": [
      "PATCH /settings/household",
      "PATCH /settings/preferences"
    ],
    "cluster": {
      "entity": "settings",
      "screen": "SetupRoute"
    },
    "why": {
      "writes": 0,
      "reads": 7,
      "span": [
        "allergen",
        "auth",
        "settings"
      ]
    }
  }
];
