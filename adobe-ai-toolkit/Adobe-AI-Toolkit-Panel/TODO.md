# TODO: Panel <-> Backend Connectivity Check

- [x] Add connectivity probe UI to `test-preview.html` (connected / not connected / checking + details).
- [x] Add startup connectivity probe to `uxp-premiere-pro-samples/my-logic.js` and update panel status UI.
- [x] Choose probe strategy: try `GET /health`, if fails then try `GET /` (best-effort).

- [ ] Run backend on `localhost:8000` and verify both the browser preview and the UXP panel show correct connectivity state.

- [ ] If backend does not expose `/health` and `/` is not valid, adjust probe endpoint after observing failure details.
