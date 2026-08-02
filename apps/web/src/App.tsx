import { useState } from "react";
import { QueryForm } from "./components/QueryForm";
import { AnswerView } from "./components/AnswerView";
import { submitQuery, type Answer } from "./api/advisorApiClient";

const DEV_USER_ID = "00000000-0000-0000-0000-000000000101";
const DEV_WORKSPACE_ID = "00000000-0000-0000-0000-000000000201";

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
      const answer = await submitQuery({
        devUserId: DEV_USER_ID,
        workspaceId: DEV_WORKSPACE_ID,
        jurisdictionId,
        text
      });
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
      {state.status === "ready" && <AnswerView answer={state.answer} />}
    </main>
  );
}
