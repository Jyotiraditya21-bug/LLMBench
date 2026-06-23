# Phase 9: Branding Palette, Dynamic Table Interactions, Scroll Transitions & GitHub Pages CI/CD

This document details the branding implementation, custom UI scrollable animations, client-side sorting/filtering, and automated GitHub Pages pipeline updates delivered during Phase 9.

---

## 1. Summary of Files Created & Modified

1. **[frontend/.streamlit/config.toml](file:///Users/jimmycodes/LLMBench/frontend/.streamlit/config.toml) [NEW]:** Standardizes global Streamlit variables to lock the custom green branding palette across all subpages.
2. **[frontend/utils/ui.py](file:///Users/jimmycodes/LLMBench/frontend/utils/ui.py) [NEW]:** Injects global CSS for custom scrollbars, webkit scroll animations, font overrides (`Outfit` and `Inter`), hides default Streamlit branding, and formats Plotly chart templates.
3. **[frontend/app.py](file:///Users/jimmycodes/LLMBench/frontend/app.py) [MODIFY]:** Integrates the UI helper, adds runtime path resolution, removes emojis, and styles the Cost vs Quality frontier scatter plot.
4. **[frontend/pages/01_datasets.py](file:///Users/jimmycodes/LLMBench/frontend/pages/01_datasets.py) [MODIFY]:** Connects the shared styling engine, removes emojis, and adds runtime path resolution.
5. **[frontend/pages/02_prompt_arena.py](file:///Users/jimmycodes/LLMBench/frontend/pages/02_prompt_arena.py) [MODIFY]:** Applies custom green/mint radar charts, removes emojis, and adds runtime path resolution.
6. **[frontend/pages/03_eval_hub.py](file:///Users/jimmycodes/LLMBench/frontend/pages/03_eval_hub.py) [MODIFY]:** Adds custom UI styling overrides, removes emojis, and adds runtime path resolution.
7. **[frontend/pages/04_rca_console.py](file:///Users/jimmycodes/LLMBench/frontend/pages/04_rca_console.py) [MODIFY]:** Connects custom layout styles, removes emojis, and adds runtime path resolution.
8. **[frontend/pages/05_cost_analytics.py](file:///Users/jimmycodes/LLMBench/frontend/pages/05_cost_analytics.py) [MODIFY]:** Applies new green bar charts, removes emojis, and adds runtime path resolution.
9. **[backend/app/templates/report.html](file:///Users/jimmycodes/LLMBench/backend/app/templates/report.html) [MODIFY]:** Purges all emojis, adds a sticky header, custom scrollbars, scroll sections with IntersectionObserver fade-in transitions, and integrates interactive client-side column sorting, model filtering, and quick text search.
10. **[backend/app/workers/report_generator.py](file:///Users/jimmycodes/LLMBench/backend/app/workers/report_generator.py) [MODIFY]:** Resolves the loop reuse issue by consolidating database queries inside a single event loop, and re-targets the output directory to root `docs/`.
11. **[.github/workflows/ai_quality_gate.yml](file:///Users/jimmycodes/LLMBench/.github/workflows/ai_quality_gate.yml) [MODIFY]:** Appends report compilation and static page deployment to the `gh-pages` branch.

---

## 2. Core Branding Palette Specs

To align our products visually, the user interface enforces a specific nature-centric, forest-green branding palette:

- **Deep Forest Green (`#142718`):** Applied as primary background colors for dashboards and reports.
- **Pine Green (`#2E5B41`):** Applied as container headers, sub-elements, table borders, and card frames.
- **Sage Green (`#98CBB0`):** Used as high-contrast accents, main charts boundary lines, and primary badge values.
- **Light Mint/Cream (`#E7EFE4`):** Main text label and primary headline visual highlights.

---

## 3. Core Code Section Explanations

### Consolidated Single Event Loop compiler
```python
async def main():
    target_id = None
    if len(sys.argv) > 1:
        try: target_id = int(sys.argv[1])
        except ValueError: pass

    if target_id is None:
        target_id = await get_latest_run_id()

    await compile_report(target_id)

if __name__ == "__main__":
    asyncio.run(main())
```
- **Like I am 5 years old 🧸:** When the helper goes to the store, he is only allowed to use one checkout lane (event loop). If he tries to split up his items into two lanes, the card reader gets confused and stops working (Event loop closed). By doing all checkout steps in one lane, it runs perfectly!
- **Industry Relevance 🚀:** SQLAlchemy's async engine maintains connection pools bound to the thread's active event loop. Spawning multiple calls to `asyncio.run()` closes the first loop, causing subsequent queries on the same connection objects to throw connection errors. Consolidating logic into a single entry loop ensures full synchrony and pool longevity.
- **Interview Relevance 🎤:** *Why does calling `asyncio.run` multiple times in a script lead to `RuntimeError: Event loop is closed` in async database connections?* Each call to `asyncio.run` constructs, runs, and terminates a fresh event loop. Async database drivers instantiate connections that tie back to the loop they were constructed in. Reusing the driver after the loop closes throws futures errors. The correct implementation is to combine the entry routines in a single coroutine and call `asyncio.run` exactly once at the entry-point.

---

### Scroll Entrance Animation (Intersection Observer)
```javascript
const observer = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            observer.unobserve(entry.target);
        }
    });
}, { threshold: 0.05 });

document.querySelectorAll(".scroll-section").forEach(section => {
    observer.observe(section);
});
```
- **Like I am 5 years old 🧸:** A little scout stands on top of the hill. He watches as the boxes slide down. As soon as a box gets close enough to see (enters the viewport), he waves his wand to open the box and make it grow (triggers CSS slide/fade transitions).
- **Industry Relevance 🚀:** Hardcoding animation properties triggers animations immediately upon page load, which is wasted on components positioned below the fold. An Intersection Observer detects viewport intersections dynamically, triggering premium CSS keyframe entries exactly as the user scrolls, boosting user experience and lowering rendering lag.
- **Interview Relevance 🎤:** *How do you optimize scroll animations for performance on heavy web pages?* Instead of binding to high-frequency scroll event listeners that block the main thread, we use `IntersectionObserver`. It monitors element visibility asynchronously, only adding action classes when elements intersect the viewport, which avoids layout thrashing.
