# Baserow Chunks Table Setup Guide

## Overview

The **Chunks** table is the central metadata repository for the Parent-Child chunking architecture. It stores all chunks (header, parent, and child) with rich metadata for human annotation, surgical filtering, and data quality improvement.

## Manual Table Creation

Due to Baserow API limitations with table creation permissions, create the table manually:

1. Open Baserow at http://localhost:8080
2. Navigate to the Stellar Sales System database (ID: 174)
3. Click "+ Add table"
4. Name it: **Chunks**
5. Note the Table ID from the URL (e.g., http://localhost:8080/database/174/table/709/)
6. Add `BASEROW_CHUNKS_ID=709` to your `.env` file

## Field Schema

Create the following fields in the Chunks table:

### Core Identifiers

| Field Name | Type | Description | Required |
|------------|------|-------------|----------|
| `chunk_id` | Text | UUID (primary key) | ✅ Yes |
| `parent_id` | Text | UUID of parent chunk (null for parents/header) | No |
| `chunk_type` | Single Select | "header", "parent", or "child" | ✅ Yes |
| `external_id` | Number | Transcript ID from header | ✅ Yes |
| `transcript_filename` | Text | Source filename | ✅ Yes |

**chunk_type options:**
- `header` (Blue)
- `parent` (Green)
- `child` (Orange)

### Content

| Field Name | Type | Description |
|------------|------|-------------|
| `text` | Long Text | Chunk content (speaker turn or phase segment) |

### Speaker Metadata (Child Chunks Only)

| Field Name | Type | Description |
|------------|------|-------------|
| `speaker_name` | Text | Speaker identifier (e.g., "Joshua Vaughan (Sales Rep)") |
| `start_time` | Number (1 decimal) | Seconds from recording start |
| `end_time` | Number (1 decimal) | Seconds from recording end |

### Sales Metadata (Human Editable! ✅)

| Field Name | Type | Description | Editable |
|------------|------|-------------|----------|
| `sales_stage` | Single Select | Discovery/Demo/Objection Handling/Closing | ✅ Yes |
| `conversation_phase` | Text | Granular phase label | ✅ Yes |
| `detected_topics` | Long Text | JSON array of keywords/topics | ✅ Yes |

**sales_stage options:**
- `Discovery` (Blue)
- `Demo` (Green)
- `Objection Handling` (Red)
- `Closing` (Yellow)
- `Unknown` (Light Gray)

### Semantic NLP Metadata (Human Editable! ✅)

| Field Name | Type | Description | Editable |
|------------|------|-------------|----------|
| `intent` | Single Select | question/statement/objection/agreement/proposal/clarification | ✅ Yes |
| `sentiment` | Single Select | positive/neutral/negative/concerned/excited | ✅ Yes |
| `discourse_marker` | Single Select | transition/confirmation/hedge/emphasis/none | ✅ Yes |
| `contains_entity` | Checkbox | Entity presence flag | ✅ Yes |

**intent options:**
- `question` (Blue)
- `statement` (Green)
- `objection` (Red)
- `agreement` (Yellow)
- `proposal` (Orange)
- `clarification` (Light Blue)

**sentiment options:**
- `positive` (Green)
- `neutral` (Light Gray)
- `negative` (Red)
- `concerned` (Orange)
- `excited` (Yellow)

**discourse_marker options:**
- `transition` (Blue)
- `confirmation` (Green)
- `hedge` (Orange)
- `emphasis` (Red)
- `none` (Light Gray)

### Parent Chunk Metadata

| Field Name | Type | Description |
|------------|------|-------------|
| `turn_count` | Number (0 decimals) | Number of speaker turns in parent |
| `speaker_balance` | Number (2 decimals) | Client-to-rep ratio (0.0 to 1.0) |

### Timestamps

| Field Name | Type | Description |
|------------|------|-------------|
| `timestamp_start` | Text | HH:MM:SS format |
| `timestamp_end` | Text | HH:MM:SS format |

## Human-in-the-Loop Workflow

The key value of this table is **human annotation and quality improvement**:

### Use Cases

1. **Correct Mislabeled Sales Stages**
   - Analyst reviews chunks and corrects sales_stage from "Demo" to "Objection Handling"
   - Next retrieval uses corrected stage for better filtering

2. **Enhance Topic Detection**
   - Add missing topics to `detected_topics` field
   - Remove irrelevant machine-detected topics

3. **Fix Intent/Sentiment Errors**
   - Correct "statement" to "objection" when LLM misclassified
   - Adjust sentiment from "neutral" to "concerned"

4. **Data Quality Audits**
   - Filter by sales_stage to review all "Closing" chunks
   - Ensure consistent labeling across transcripts

5. **Training Data Generation**
   - Export corrected chunks for fine-tuning classification models
   - Build gold standard dataset for evaluation

## Integration Points

- **Ingestion Pipeline**: PersistenceAgent syncs all chunks to this table after processing
- **Retrieval**: QdrantRAGMixin can optionally sync corrections back to Qdrant
- **Analytics**: Export to CSV for analysis in Excel/Python
- **Reporting**: Filter and group by sales_stage, intent, sentiment for coaching insights

## Next Steps

1. Create the table manually in Baserow UI
2. Add `BASEROW_CHUNKS_ID` to `.env`
3. Run a test transcript through the pipeline
4. Verify chunks are synced to Baserow
5. Practice editing metadata in the Baserow interface
