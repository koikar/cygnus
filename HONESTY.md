# HONESTY.md

> Mandatory disclosure for the hackathon. This file lives at the root of the
> repository. Judges can cross-check it against the code, git history, and the
> technical video.
>
> Disclosed shortcuts are not hidden. This file explains what is real, what is
> mocked, what was external, what was AI-assisted, and what is still future work.

---

## 1. Team - who did what

Judges compare this against `git shortlog -sn`, so keep it honest.

```text
 1 Aaron Koivunen
 2 Muhammad Afzaal Afzal
 3 Adriana Carmona
 4 Areej Anjum
```

Important context: before this hackathon, our team had no hands-on robotics
background. During the hackathon we learned the SO-101/LeRobot stack, adapted it
into an MCP tool interface, and used LLM/agent tooling to help build and debug
the system. Everyone contributed ideas and review across the project, especially
around how to make the robot task understandable to an agent through a grid/zone
abstraction.

| Member                | GitHub handle         | Main contributions                                                                                                                                                                 |
| --------------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Aaron Koivunen        | @koikar               | Led the Python robot/MCP implementation with Claude Code assistance: MCP server, agent loop, simulator, SO-101 backend path, safety guardrails, skills, tests, and technical docs. |
| Muhammad Afzaal Afzal | Confirm before submit | Built the ReflexOS website, reviewed architecture/system design, suggested technical improvements, and helped debug/fix issues across the repo.                                    |
| Adriana Carmona       | Confirm before submit | Improved repo quality, helped fix bugs, contributed to product/pitch clarity, and handled pitch video work.                                                                        |
| Areej Anjum           | Confirm before submit | Built the web app / 3D simulation demo experience and contributed the grid/zone idea that made the robot task easier for an agent to reason about.                                 |

If the missing GitHub handles differ from the git identities, fill them in before
final submission. The contribution descriptions above are based on team
discussion plus the current repository state.

---

## 2. What is fully working

Features that run end-to-end with real project logic:

- **Offline training-loop demo**: `python -m reflexos demo` / tests run the
  simulator, execute pick-and-place episodes, detect a novel cube zone, escalate
  once, learn the correction, and replay the same case as a cheaper reflex.
- **Robot MCP server**: `reflexos.server` exposes the robot as MCP tools for
  state/perception, guarded joint/Cartesian/gripper actions, teaching, skill
  save/replay, calibration, and skill audit/listing.
- **Agent-friendly robot abstraction**: the project turns robot operation into
  safe named tools and grid/zone-based tasks rather than raw uncontrolled motor
  commands. This is the main technical idea we built during the hackathon.
- **Simulator backend**: `reflexos.robot.sim.SimBackend` runs without hardware or
  network and models enough pick-and-place behavior to validate the learning
  claim.
- **SO-101 backend code path**: `reflexos.robot.so101.SO101Backend` is
  implemented for connecting to a real SO-101 follower through LeRobot. Live
  operation still depends on correct hardware, calibration, power, camera
  permissions, and safe workspace setup, so the automated verification is the
  simulator/test path rather than a guaranteed live robot run.
- **Safety guardrails**: joint targets are clamped, unknown joint keys are
  dropped, out-of-workspace Cartesian targets fail closed, and concurrent
  motion is serialized through a process-wide motion lock.
- **Saved skill library**: `skills/*.json` stores taught poses, grab/drop
  routines, composed routines, and archived probes. `audit_skills()` validates
  active skills against the current body schema.
- **Camera-to-table calibration helper**: calibration fitting and projection
  logic is implemented and tested locally.
- **ReflexOS website**: `website/` is a custom business/product site explaining
  the problem, market value, architecture, and go-to-market story. Deployed live
  at [reflexos-six.vercel.app](https://reflexos-six.vercel.app/).
- **3D mission-control demo UI**: `live-robot-demo/` builds and runs as a
  visual explanation of the fail -> recover -> learn -> replay loop.
- **Build/test verification**: the Python tests and both frontend production
  builds pass locally:

```bash
uv run pytest -q
npm --prefix website run build
npm --prefix live-robot-demo run build
```

Latest observed results: Python tests passed with `17 passed, 1 warning`; both
frontend builds completed successfully.

---

## 3. What is mocked, stubbed, or hardcoded

Every shortcut:

| What is faked                                                            | Where (file:line or folder)                                                                                              | Why we mocked it                                                                                          | What the real version would do                                                                                                            |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Mission-control demo sequence is scripted/mock-first.                    | `live-robot-demo/src/App.jsx:27`, `live-robot-demo/src/mock/mockEngine.js:3`, `live-robot-demo/src/mock/mockSequence.js` | Gives judges a stable visual demo even when robot hardware, venue network, or cameras are unavailable.    | Stream live robot state, tool calls, reasoning, camera events, and learned-skill metrics from the Python MCP server or a backend adapter. |
| Live demo UI backend is optional and not the primary robot control path. | `live-robot-demo/src/client/backendClient.js:1`, `live-robot-demo/src/App.jsx:36`                                        | We focused the working robot/control path in Python MCP first, while keeping the UI useful for the pitch. | Provide a real HTTP/WebSocket service that proxies the MCP robot server and emits live events to the UI.                                  |
| Local System-2 fallback is scripted when no API credentials are present. | `reflexos/cognition/reasoning.py:33`, `reflexos/cognition/reasoning.py:98`                                               | Keeps the training-loop proof runnable offline, deterministic, and judge-verifiable without API keys.     | Use a vision-capable hosted reasoning model with real camera/image input and structured tool planning.                                    |
| Simulator uses simplified ground-truth scene state.                      | `reflexos/robot/sim.py:1`, `reflexos/robot/sim.py:47`                                                                    | Allows repeatable tests without requiring a powered robot arm for every run.                              | Use live camera frames, detector output, joint state, and gripper feedback from the robot.                                                |
| Real SO-101 structured scene extraction is not complete.                 | `reflexos/robot/so101.py:9`, `reflexos/robot/so101.py:96`                                                                | Hardware integration time was limited, and our team was learning robotics during the hackathon.           | Convert camera frames into a reliable structured scene using vision detection/calibration.                                                |
| Hosted cognition backend is a stub.                                      | `reflexos/cognition/hosted.py:11`, `reflexos/cognition/hosted.py:36`                                                     | The verified path is local; hosted durable memory/fleet learning was not finished.                        | Open an MCP client session to the hosted cognitive kernel for recall, rationale writing, learning, and skill registration.                |
| Product website claims are pitch/business content, not production proof. | `website/`                                                                                                               | Needed for the business video and to explain the opportunity clearly.                                     | Back each product claim with production telemetry, customer deployments, and live fleet integrations.                                     |

---

## 4. External APIs, services & data sources

Everything the project calls or can call:

| Service / API / dataset                                  | Used for                                                                   | Real call or mocked?                                                         | Auth (sandbox / test key / none)                                                 |
| -------------------------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| SO-101 / SO-ARM100 hardware through Hugging Face LeRobot | Real robot motion, servo bus access, calibration, and camera observation.  | Real when hardware is connected; absent in simulator.                        | None for local hardware; requires physical device, power, and calibration files. |
| Model Context Protocol Python SDK                        | Exposes the robot as MCP tools over stdio or streamable HTTP.              | Real library.                                                                | None.                                                                            |
| OpenAI / Azure OpenAI SDK                                | Optional online reasoner in `LLMReasoner`.                                 | Real call only if credentials are present; otherwise falls back to scripted. | `OPENAI_API_KEY` or Azure OpenAI env vars.                                       |
| Claude Code / LLM coding assistant                       | Helped generate, iterate, and debug parts of the MCP/agent implementation. | Real development assistance, not a runtime service required by the app.      | Developer tool access, no app runtime auth.                                      |
| OpenCV / UVC camera                                      | Wrist/scene camera frames for robot perception.                            | Real when camera index is configured; simulator uses structured scene state. | OS camera permission, no API key.                                                |
| `placo` / URDF tooling                                   | FK/IK and joint-effect calculations for SO-101.                            | Real local library.                                                          | None.                                                                            |
| SQLite via Python stdlib                                 | Local reflex/rationale memory.                                             | Real local storage; tests default to in-memory.                              | None.                                                                            |
| Next.js / Vite / React / Three.js / Recharts             | Website and 3D mission-control demo UI.                                    | Real UI frameworks; `live-robot-demo` data defaults to mock sequence.        | None.                                                                            |

---

## 5. Pre-existing code

Anything written before kickoff that we brought into this project: prior personal
projects, forked open-source code, templates, boilerplate, internal libraries.

| Item                                             | Source (URL or description)                                                                                                            |                                                                       Roughly how much | License                           |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------: | --------------------------------- |
| Project-specific repository code                 | Git history starts on 2026-06-06 with `Initial commit: Cygnus`; the project was renamed/repositioned as ReflexOS during the hackathon. | All project-specific source currently in this repo appears in hackathon-dated commits. | MIT for this repo.                |
| Next.js scaffold/boilerplate                     | `create-next-app` style project in `website/`.                                                                                         |   Framework scaffold and config; page/components/content were customized for ReflexOS. | Next.js/React ecosystem licenses. |
| Vite React scaffold/boilerplate                  | Vite-style project in `live-robot-demo/`.                                                                                              |     Framework scaffold and config; 3D demo UI/components were customized for ReflexOS. | Vite/React ecosystem licenses.    |
| External open-source dependencies                | Listed in `pyproject.toml`, `website/package.json`, and `live-robot-demo/package.json`.                                                |                                 Dependency code is external, not authored by the team. | See each dependency license.      |
| SO-101 hardware designs and LeRobot driver stack | SO-ARM100/SO-101 and Hugging Face LeRobot ecosystem.                                                                                   |                                       Hardware platform and driver stack are external. | See upstream projects.            |

We are not claiming to have invented the robot hardware, the LeRobot driver
stack, MCP itself, or the frontend frameworks. Our work was adapting these pieces
into an agent-operable robot training prototype with a business/demo surface.

---

## 6. Known limitations & next steps

- Confirm the missing GitHub handles in the team table before submitting.
- We were new to robotics and built this under hackathon time constraints; the
  code is a prototype, not a production robotics platform.
- `live-robot-demo/` is mock-first and should be presented as an explanation UI,
  not as the primary live hardware controller.
- The verified backend proof is local/simulated plus code paths for real
  hardware. Real-arm operation still depends on correct SO-101 power,
  calibration, camera permissions, and safe workspace setup.
- Real camera-to-scene understanding on the SO-101 path is incomplete.
- Hosted cognition/fleet memory is not complete; local memory and the
  scripted/LLM reasoner path are the working proof.
- The current robot loop is deliberate MCP tool-call control, not a trained
  30 Hz robot policy.
- Open-loop replayed skills still need perception and verification for changed
  scenes.
- `npm install` reports 2 moderate dependency vulnerabilities in both frontend
  folders; do not run `npm audit fix --force` blindly right before submission
  because it may introduce breaking dependency changes.
- `live-robot-demo` build succeeds but warns that some generated chunks exceed
  500 kB after minification.
- `live-robot-demo` install warns that `three-mesh-bvh@0.7.8` is deprecated due
  to Three.js version compatibility.
- `live-robot-demo` install also warns that `recharts@2.15.4` is on an inactive
  release branch.
- Next steps: wire a real WebSocket event backend for the demo UI, finish hosted
  cognition, improve live vision/perception, reduce frontend bundle size,
  address dependency audit warnings, and add live hardware evidence
  links/screenshots to the README.
