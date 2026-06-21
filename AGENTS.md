# Repository Instructions

## Role

Build this repository as a maintainable public information automation platform.
Prioritize readable names, small modules, testable logic, and clear operational
boundaries.

## Project Direction

The service collects Daegu public information from RSS/API sources, transforms it
into citizen-friendly content with AI, and publishes it to social channels through
automated workflows.

Initial source categories:

- Daegu recruitment and exams
- Daegu contests and participant recruitment
- Daegu startup support
- Daegu business support

## Engineering Principles

- Use descriptive names that match the public information domain.
- Keep source collection, content generation, publishing, storage, and reporting
  in separate modules.
- Add new public data sources through isolated adapters.
- Keep secrets in environment variables or GitHub Secrets, never in source.
- Write unit tests for parsing, normalization, duplicate detection, and channel
  failure handling.
- Use comments only to explain non-obvious design or operational constraints.
