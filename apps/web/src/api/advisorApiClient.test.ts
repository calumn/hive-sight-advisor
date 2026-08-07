import { afterEach, describe, expect, it, vi } from "vitest";
import { submitCorrection, submitQuery } from "./advisorApiClient";

describe("submitQuery", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends the request with no auth header and the correct body, and parses the answer", async () => {
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
      jurisdictionId: "jurisdiction-1",
      text: "How do I treat varroa?"
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/queries$/);
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({ "content-type": "application/json" });
    expect(JSON.parse(init.body)).toEqual({
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

  it("throws the server's detail.message when the guest rate limit is exceeded", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: {
              reason: "guest_rate_limit_exceeded",
              message: "Guest query limit reached for this hour. Sign in for higher limits."
            }
          }),
          { status: 429 }
        )
      )
    );

    await expect(
      submitQuery({ jurisdictionId: "jurisdiction-1", text: "How do I treat varroa?" })
    ).rejects.toThrow("Guest query limit reached for this hour. Sign in for higher limits.");
  });

  it("sends an authorization header when a token is provided", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "answer-1",
          query_id: "query-1",
          text: "Treat varroa with oxalic acid.",
          grounding_status: "grounded",
          citations: []
        }),
        { status: 200 }
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    await submitQuery({
      jurisdictionId: "jurisdiction-1",
      text: "How do I treat varroa?",
      token: "google-id-token"
    });

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers).toEqual({
      "content-type": "application/json",
      authorization: "Bearer google-id-token"
    });
  });
});

describe("submitCorrection", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends the request with a bearer token and the correct body, and parses the response", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ id: "correction-1", answer_id: "answer-1", status: "trusted" }),
        { status: 200 }
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    const correction = await submitCorrection({
      token: "google-id-token",
      answerId: "answer-1",
      notes: "This cites the wrong jurisdiction's guidance."
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/corrections$/);
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({
      "content-type": "application/json",
      authorization: "Bearer google-id-token"
    });
    expect(JSON.parse(init.body)).toEqual({
      answer_id: "answer-1",
      notes: "This cites the wrong jurisdiction's guidance."
    });

    expect(correction).toEqual({ id: "correction-1", answerId: "answer-1", status: "trusted" });
  });

  it("throws the server's detail message when the request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Sign in required." }), {
          status: 401
        })
      )
    );

    await expect(
      submitCorrection({
        token: "google-id-token",
        answerId: "answer-1",
        notes: "Something is wrong."
      })
    ).rejects.toThrow("Sign in required.");
  });
});
