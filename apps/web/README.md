# Pokomon Web

Next.js frontend for the paper companion agent.

## Run

```bash
npm install
npm run dev
```

## Notes

- The UI is wired to the FastAPI backend.
- Formula rendering uses `react-markdown + remark-math + rehype-katex`.
- Upload, overview, and chat flows are connected to the backend API.
