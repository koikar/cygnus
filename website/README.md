# ReflexOS Website

This is the public/product website for ReflexOS, built with Next.js, React,
Tailwind, and Motion. It is a communication surface for the hackathon pitch; the
robot implementation lives in the root `reflexos/` Python package.

## Getting Started

Install dependencies and run the development server from this directory:

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Useful Commands

```bash
npm run lint
npm run build
```

## Scope

This website is not the robot control path. Use the root README for the MCP
server, SO-101 setup, simulation demo, and safety notes:

```bash
cd ..
uv run python -m reflexos demo
bash scripts/run_robot.sh
```

See also root `HONESTY.md` for what is functional, mocked, and external.

## Deployment

Any standard Next.js host works. For Vercel, deploy the `website/` directory as
the project root and run `npm run build`.
