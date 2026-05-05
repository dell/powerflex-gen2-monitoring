# How to Contribute

We welcome contributions to this project. This document provides guidelines for contributing.

## Table of Contents

- [Report Bugs](#report-bugs)
- [Feature Requests](#feature-requests)
- [Your First Contribution](#your-first-contribution)
- [Submitting Changes](#submitting-changes)
- [Coding Guidelines](#coding-guidelines)
- [Commit Messages](#commit-messages)

## Report Bugs

Before submitting a bug report, check the existing issues to see if the problem has already been reported.

When opening a bug report, include:
1. Version of the monitoring tools, Telegraf, InfluxDB, Grafana, and Python
2. PowerFlex version and generation (Gen1/Gen2)
3. Steps to reproduce the issue
4. Expected vs. actual behavior
5. Relevant log output (from `/var/log/messages` or manual script execution)

**Note:** Do not include private company information, IP addresses, or credentials in bug reports.

## Feature Requests

Feature requests are welcome. Open an issue describing the feature you'd like to see, why you need it, and how it should work.

## Your First Contribution

Unsure where to begin? Look for issues labeled `good first issue` or `help wanted`.

## Submitting Changes

1. Fork the repository
2. Create a branch from `main` for your changes
3. Make your changes and test them
4. Commit your changes with a clear commit message
5. Push your branch and open a Pull Request

### Pull Request Guidelines

- Link the PR to a related issue when applicable
- Describe what your change does and why
- Include any testing you performed
- Keep PRs focused — one fix or feature per PR

## Coding Guidelines

### Python
- Follow PEP 8 style conventions
- Maintain compatibility with Python 3.9+
- Test scripts manually against a PowerFlex cluster when possible

### Shell Scripts
- Use `#!/usr/bin/env bash` as the shebang line
- Include the standard Apache 2.0 copyright header
- Quote variables to prevent word splitting

## Commit Messages

Use clear, descriptive commit messages:

```
Short summary of the change (50 chars or less)

Optional longer description explaining what and why (not how).
Wrap at 72 characters.
```

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

## Developer Certificate of Origin

By contributing to this project, you agree that your contributions are your own original work (or you have the right to submit them) and that you grant Dell, Inc. a perpetual, worldwide, non-exclusive, royalty-free license to use your contributions as part of this project under the Apache License 2.0.
