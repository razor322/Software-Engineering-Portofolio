module.exports = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "type-enum": [
      2,
      "always",
      [
        "feat",
        "fix",
        "docs",
        "style",
        "refactor",
        "perf",
        "test",
        "chore",
        "build",
        "ci",
        "revert"
      ]
    ],
    "subject-case": [2, "always", ["lower-case"]],
    "header-max-length": [2, "always", 140],
    "body-max-line-length": [2, "always", 70],
    // ponytail: guide's "scope-empty: never" forces a scope, breaking guide's own Step 8 example — scope optional instead
  }
};
