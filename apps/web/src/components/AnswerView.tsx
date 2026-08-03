import { type FormEvent, useState } from "react";
import { submitCorrection, type Answer } from "../api/advisorApiClient";

export type AnswerViewProps = {
  answer: Answer;
  devUserId: string;
  workspaceId: string;
};

export function AnswerView({ answer, devUserId, workspaceId }: AnswerViewProps) {
  const [isFlagFormOpen, setIsFlagFormOpen] = useState(false);
  const [notes, setNotes] = useState("");
  const [submissionState, setSubmissionState] = useState<
    "idle" | "submitting" | "submitted" | "error"
  >("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmitCorrection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedNotes = notes.trim();
    if (trimmedNotes.length === 0) {
      return;
    }
    setSubmissionState("submitting");
    try {
      await submitCorrection({
        devUserId,
        workspaceId,
        answerId: answer.id,
        notes: trimmedNotes
      });
      setSubmissionState("submitted");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Something went wrong.");
      setSubmissionState("error");
    }
  }

  function handleFlagAgain() {
    setNotes("");
    setSubmissionState("idle");
    setErrorMessage(null);
    setIsFlagFormOpen(true);
  }

  return (
    <section className={`answer-view answer-view-${answer.groundingStatus}`}>
      {answer.groundingStatus === "ungrounded" && (
        <p className="answer-banner answer-banner-ungrounded">
          No grounded answer found for this jurisdiction.
        </p>
      )}
      {answer.groundingStatus === "partial" && (
        <p className="answer-banner answer-banner-partial">
          This may not directly answer your question — closest related guidance:
        </p>
      )}
      <p className="answer-text">{answer.text}</p>
      <div className="answer-status">Grounding: {answer.groundingStatus}</div>
      {answer.citations.length > 0 && (
        <ul className="answer-citations">
          {answer.citations.map((citation) => (
            <li key={citation.passageId} className="citation">
              <span className="citation-title">{citation.documentTitle}</span>
              {" — "}
              {citation.documentSourceUrl ? (
                <a href={citation.documentSourceUrl} target="_blank" rel="noreferrer">
                  {citation.documentSource}
                </a>
              ) : (
                <span>{citation.documentSource}</span>
              )}
              {" "}
              <span className="citation-licence">({citation.documentLicenceTerms})</span>
              {citation.isSuperseded && (
                <p className="citation-superseded-warning">
                  This source has been superseded
                  {citation.supersededByDocumentTitle
                    ? ` by "${citation.supersededByDocumentTitle}"`
                    : ""}
                  {" "}— treat this guidance as outdated, not current.
                </p>
              )}
            </li>
          ))}
        </ul>
      )}

      <div className="answer-correction">
        {submissionState === "submitted" ? (
          <div className="correction-ack">
            <p>Thanks — recorded.</p>
            <button type="button" onClick={handleFlagAgain}>
              Flag again
            </button>
          </div>
        ) : isFlagFormOpen ? (
          <form onSubmit={handleSubmitCorrection} className="correction-form">
            <label htmlFor="correction-notes">What&apos;s wrong with this answer?</label>
            <textarea
              id="correction-notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              disabled={submissionState === "submitting"}
              rows={2}
            />
            <button
              type="submit"
              disabled={submissionState === "submitting" || notes.trim().length === 0}
            >
              {submissionState === "submitting" ? "Submitting..." : "Submit"}
            </button>
            {submissionState === "error" && <p className="correction-error">{errorMessage}</p>}
          </form>
        ) : (
          <button type="button" onClick={() => setIsFlagFormOpen(true)}>
            Flag as wrong
          </button>
        )}
      </div>
    </section>
  );
}
