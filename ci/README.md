# ci/

CI/CD pipeline configuration (GitLab CI).

## Cấu trúc

```
ci/
└── pipeline.yml    # GitLab CI pipeline: lint → test → build → deploy
```

## File

| File | Vai trò |
|------|---------|
| `pipeline.yml` | 4-stage GitLab CI pipeline. Tất cả commands dùng `uv run`. Build Docker images cho Spark, Flink, Dagster. Deploy qua ArgoCD sync. |

## Pipeline stages

```
lint ──→ test ──→ build ──→ deploy
 │         │        │         │
 │         │        │         └── ArgoCD sync (dev auto, prod manual)
 │         │        └── docker build + push (spark, flink, dagster)
 │         └── pytest + dbt test
 └── ruff check
```

## Triggers

- **Push to main:** full pipeline (lint → test → build → deploy to dev)
- **Merge request:** lint + test only
- **Tag (v*.*):** deploy to prod (manual approval gate)
