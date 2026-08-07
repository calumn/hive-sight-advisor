import { useState } from "react";
import { QueryForm } from "./components/QueryForm";
import { AnswerView } from "./components/AnswerView";
import { submitQuery, type Answer } from "./api/advisorApiClient";

// Every /queries request is unauthenticated (Slice 0013) and resolves server-side
// to the well-known Guest Workspace, so a submitted Answer is always owned by it —
// the correction flow below must reference the same identity to locate that Answer.
const GUEST_USER_ID = "00000000-0000-0000-0000-000000000901";
const GUEST_WORKSPACE_ID = "00000000-0000-0000-0000-000000000902";

type RequestState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; answer: Answer }
  | { status: "error"; message: string };

export function App() {
  const [state, setState] = useState<RequestState>({ status: "idle" });

  async function handleSubmit(text: string, jurisdictionId: string) {
    setState({ status: "loading" });
    try {
      const answer = await submitQuery({ jurisdictionId, text });
      setState({ status: "ready", answer });
    } catch (error) {
      setState({
        status: "error",
        message: error instanceof Error ? error.message : "Something went wrong."
      });
    }
  }

  return (
    <main className="app">
      <h1>HiveSight Advisor</h1>
      <p className="tagline">Ask a beekeeping question and get a grounded answer with a citation.</p>
      <QueryForm onSubmit={handleSubmit} disabled={state.status === "loading"} />
      {state.status === "error" && <p className="error">{state.message}</p>}
      {state.status === "ready" && (
        <AnswerView answer={state.answer} devUserId={GUEST_USER_ID} workspaceId={GUEST_WORKSPACE_ID} />
      )}
    </main>
  );
}
