# Architecture

```text
React + Vite
    |
    | HTTP / JSON + multipart upload
    v
FastAPI
    |---- SQLAlchemy ---- SQLite (video metadata, QC checks, reviews)
    |
    |---- Local filesystem (original video files)
    |
    `---- OpenCV QC service (metadata, decode, blur and dark-frame heuristics)
```

The automated QC result and human review decision are separate fields. Passing QC does not automatically approve a video; a human reviewer records the final decision.
