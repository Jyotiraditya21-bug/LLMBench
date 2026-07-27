# LLMBench Version 1

## What Version 1 Does

LLMBench Version 1 is a platform for testing and comparing Large Language Models.

Its main features are:

- Create datasets containing questions and expected answers.
- Save and version prompt templates.
- Run the same tests against OpenAI, Anthropic, and Gemini models.
- Score answers for accuracy, completeness, hallucination, tone, and reasoning.
- Compare two evaluation runs to find quality, speed, and cost changes.
- Generate root-cause reports for failed answers.
- Generate adversarial test cases for red-team testing.
- Show evaluation history, charts, costs, and results in a web dashboard.
- Run evaluations in the background with Celery and Redis.
- Generate static reports and run a quality gate in GitHub Actions.

## Main Version 1 Drawbacks

- The API key is written directly in the code and browser, so it is not secure.
- Some untrusted values are inserted into HTML and can create security problems.
- Missing or failed model APIs can silently return fake results.
- The CI quality gate can pass while testing mock answers instead of real models.
- Evaluation jobs can remain stuck if the queue or database fails.
- Model execution is mostly sequential and becomes slow for large datasets.
- Model calls do not have clear timeout, retry, or cancellation rules.
- Regression reports can compare unrelated or unfinished runs.
- Deleting datasets or prompts can damage old evaluation history.
- Expensive AI-agent work runs inside normal web requests.
- Large batch imports are slow and can save only part of a batch after an error.
- Dashboard totals only use the first page of data and can become inaccurate.
- Cost calculations use hard-coded prices and estimated token counts.
- The health endpoint does not check the database, Redis, or worker.
- Database creation and Alembic migrations are both used, which can cause schema drift.
- Automated tests are limited and are not run by the CI workflow.
- Dependencies are mostly unpinned, making builds less predictable.
- The UI gives weak feedback for some failures and has accessibility gaps.
- Old `EvalForge` names remain mixed with the `LLMBench` name.

## Version 1 Summary

Version 1 proves the main product idea and demonstrates the complete evaluation flow. However, its security, reliability, data integrity, scaling, testing, and user experience are not yet suitable for a dependable production platform.
