# Baserow Import Templates

Files in this folder can be imported into Baserow to create starter tables.

## Tables
- clients.csv – primary CRM record keyed by `external_id` (your transcript header ID)
- meetings.csv – meetings linked by `client_external_id`
- deals.csv – deals linked by client/meeting `external_id`
- communications.csv – email/call notes linked by client/meeting

## Import Steps
1. Open Baserow at `http://localhost:8055` and create a new Database.
2. For each table:
   - Click “Import” → “CSV” → upload the corresponding file.
   - Enable “Use first row as field names”.
   - After import, set field types:
     - external_id fields: Text (mark as Unique if desired).
     - children_count, duration_minutes, estimated_value, win_probability: Number.
     - sent_at / meeting_date / close_date: Date.
     - comm_type / meeting_type / outcome_status: Single Select (optional).
   - Optionally create Links between tables on matching external_id fields.

## Keying Strategy
- `external_id` is the cross-system key matching your transcript header ID.
- Keep this value consistent across Postgres, Qdrant payloads, and Baserow rows.

## Notes
- These templates are minimal. You can add more fields as your workflow matures.
- If you later enable bidirectional sync, ensure webhook payloads include `external_id`. 
