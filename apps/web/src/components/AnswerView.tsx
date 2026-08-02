import type { Answer } from "../api/advisorApiClient";

export type AnswerViewProps = {
  answer: Answer;
};

export function AnswerView({ answer }: AnswerViewProps) {
  return (
    <section className="answer-view">
      <p className="answer-text">{answer.text}</p>
      <div className="answer-status">Grounding: {answer.groundingStatus}</div>
      {answer.citations.length > 0 && (
        <ul className="answer-citations">
          {answer.citations.map((citation) => (
            <li key={citation.passageId}>Source passage: {citation.passageId}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
