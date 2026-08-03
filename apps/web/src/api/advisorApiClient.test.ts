import { afterEach, describe, expect, it, vi } from "vitest";
import { submitQuery } from "./advisorApiClient";

describe("submitQuery", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends the request with dev-auth headers and the correct body, and parses the answer", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "answer-1",
          query_id: "query-1",
          text: "Treat varroa with oxalic acid.",
          grounding_status: "grounded",
          citations: [
            {
              passage_id: "passage-1",
              document_title: "Varroa Guide",
              document_source: "HBHC",
              document_source_url: "https://honeybeehealthcoalition.org/varroa/",
              document_licence_terms: "CC BY-NC-ND",
              is_superseded: false,
              superseded_by_document_title: null
            }
          ]
        }),
        { status: 200 }
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    const answer = await submitQuery({
      devUserId: "user-1",
      workspaceId: "workspace-1",
      jurisdictionId: "jurisdiction-1",
      text: "How do I treat varroa?"
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/queries$/);
    expect(init.method).toBe("POST");
    expect(init.headers).toMatchObject({
      "content-type": "application/json",
      "x-dev-user-id": "user-1"
    });
    expect(JSON.parse(init.body)).toEqual({
      workspace_id: "workspace-1",
      jurisdiction_id: "jurisdiction-1",
      text: "How do I treat varroa?"
    });

    expect(answer).toEqual({
      id: "answer-1",
      queryId: "query-1",
      text: "Treat varroa with oxalic acid.",
      groundingStatus: "grounded",
      citations: [
        {
          passageId: "passage-1",
          documentTitle: "Varroa Guide",
          documentSource: "HBHC",
          documentSourceUrl: "https://honeybeehealthcoalition.org/varroa/",
          documentLicenceTerms: "CC BY-NC-ND",
          isSuperseded: false,
          supersededByDocumentTitle: null
        }
      ]
    });
  });

  it("throws the server's detail message when the request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "No active Workspace Membership." }), {
          status: 403
        })
      )
    );

    await expect(
      submitQuery({
        devUserId: "user-1",
        workspaceId: "workspace-1",
        jurisdictionId: "jurisdiction-1",
        text: "How do I treat varroa?"
      })
    ).rejects.toThrow("No active Workspace Membership.");
  });
});
