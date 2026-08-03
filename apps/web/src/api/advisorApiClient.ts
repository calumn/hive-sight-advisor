export type Citation = {
  passageId: string;
  documentTitle: string;
  documentSource: string;
  documentSourceUrl: string | null;
  documentLicenceTerms: string;
  isSuperseded: boolean;
  supersededByDocumentTitle: string | null;
};

export type Answer = {
  id: string;
  queryId: string;
  text: string;
  groundingStatus: string;
  citations: Citation[];
};

const advisorApiUrl = import.meta.env.VITE_ADVISOR_API_URL ?? "http://localhost:8000";

export async function submitQuery({
  devUserId,
  workspaceId,
  jurisdictionId,
  text
}: {
  devUserId: string;
  workspaceId: string;
  jurisdictionId: string;
  text: string;
}): Promise<Answer> {
  const response = await fetch(`${advisorApiUrl}/queries`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-dev-user-id": devUserId
    },
    body: JSON.stringify({
      workspace_id: workspaceId,
      jurisdiction_id: jurisdictionId,
      text
    })
  });

  await ensureOk(response);
  return parseAnswer(await response.json());
}

async function ensureOk(response: Response): Promise<void> {
  if (response.ok) {
    return;
  }

  let message = `Advisor API request failed: ${response.status}`;
  try {
    const value = await response.json();
    if (isRecord(value) && typeof value.detail === "string") {
      message = value.detail;
    }
  } catch {
    // Response body wasn't JSON; fall back to the generic message above.
  }
  throw new Error(message);
}

function parseAnswer(value: unknown): Answer {
  const record = requireRecord(value, "Advisor API answer response");
  return {
    id: requireString(record.id, "id"),
    queryId: requireString(record.query_id, "query_id"),
    text: requireString(record.text, "text"),
    groundingStatus: requireString(record.grounding_status, "grounding_status"),
    citations: requireArray(record.citations, "citations").map(parseCitation)
  };
}

function parseCitation(value: unknown): Citation {
  const record = requireRecord(value, "citation");
  return {
    passageId: requireString(record.passage_id, "passage_id"),
    documentTitle: requireString(record.document_title, "document_title"),
    documentSource: requireString(record.document_source, "document_source"),
    documentSourceUrl: requireNullableString(record.document_source_url, "document_source_url"),
    documentLicenceTerms: requireString(record.document_licence_terms, "document_licence_terms"),
    isSuperseded: requireBoolean(record.is_superseded, "is_superseded"),
    supersededByDocumentTitle: requireNullableString(
      record.superseded_by_document_title,
      "superseded_by_document_title"
    )
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function requireRecord(value: unknown, field: string): Record<string, unknown> {
  if (!isRecord(value)) {
    throw new Error(`${field} was not an object`);
  }
  return value;
}

function requireArray(value: unknown, field: string): unknown[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} was not an array`);
  }
  return value;
}

function requireString(value: unknown, field: string): string {
  if (typeof value !== "string") {
    throw new Error(`${field} was not a string`);
  }
  return value;
}

function requireNullableString(value: unknown, field: string): string | null {
  if (value === null) {
    return null;
  }
  return requireString(value, field);
}

function requireBoolean(value: unknown, field: string): boolean {
  if (typeof value !== "boolean") {
    throw new Error(`${field} was not a boolean`);
  }
  return value;
}
