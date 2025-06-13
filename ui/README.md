# UI Development

This folder contains the Next.js application for the project.

## Getting Started

Install dependencies and run the development server:

```bash
npm install
npm run dev
```

The app expects an API server running locally on port `8000`. To target a different server, set the `NEXT_PUBLIC_API_BASE_URL` environment variable.

## Building for Production

Create an optimized build with:

```bash
npm run build
```

The resulting output will be placed in the `.next` directory.
