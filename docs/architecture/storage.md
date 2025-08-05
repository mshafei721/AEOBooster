# Storage Architecture

**Database:** PostgreSQL (or SQLite for local dev)

## Schema

### Users
- `id`
- `email`
- `auth_token`

### Projects
- `id`
- `user_id`
- `site_url`
- `created_at`

### Prompts
- `id`
- `project_id`
- `type`
- `text`
- `score`
- `result_text`

### Entities
- `id`
- `project_id`
- `type`
- `value`

### Reports
- `id`
- `project_id`
- `json_data`
- `pdf_link`