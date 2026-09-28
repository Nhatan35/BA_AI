export const sourceTypes = ["MEETING", "PDF", "WORD", "EXCEL", "CSV", "TEXT", "MARKDOWN", "EMAIL", "CHAT", "API_DOC", "UI", "BPMN", "REGULATION", "OTHER"];
export const classifications = ["FACT", "ASSUMPTION", "QUESTION", "DECISION", "RECOMMENDATION", "RISK", "ACTION_ITEM"];
export type Source = {
  id: string; project_id: string; source_code: string; name: string; description: string; source_type: string;
  owner: string; source_date: string | null; trust_level: string; status: string; revision: number; supersedes_source_id: string | null;
};
export type Version = {
  id: string; source_id: string; project_id: string; version_number: number; original_filename: string;
  mime_type: string; file_size: number; checksum: string; parser_status: string; parse_error: string | null;
  parser_name: string | null; parser_version: string | null; parse_run_id: string; duplicate_version_ids: string[];
};
export type Locator = {kind: string; start: number; end?: number; heading?: string; table?: number; sheet?: string; column_start?: string; column_end?: string};
export type Section = {id: string; text: string; ordinal: number; locator: Locator; display_reference: string; cells: Record<string, string>};
export type Parse = {id: string; attempt_number: number; parser_status: string; parser_name: string; parser_version: string; parse_error: string | null; metadata_json: Record<string, unknown>};
export type Parsed = {parse: Parse; items: Section[]; next_ordinal: number | null};
export type Evidence = {
  id: string; project_id: string; source_id: string; source_version_id: string; parse_run_id: string; evidence_code: string;
  evidence_type: string; classification: string; summary: string; extracted_text: string; exact_reference: string;
  locator: Locator; confidence: number | null; confirmed_by: string | null; confirmed_at: string | null; revision: number;
};
export type SearchResult = {project_id: string; source_id: string; source_name: string; source_code: string; source_status: string; source_version_id: string; version_number: number; original_filename: string; parse_run_id: string; excerpt: string; exact_reference: string};
