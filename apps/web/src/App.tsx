import { useState } from "react";
import { QueryForm } from "./components/QueryForm";
import { AnswerView } from "./components/AnswerView";
import { SignInButton } from "./components/SignInButton";
import { submitQuery, type Answer } from "./api/advisorApiClient";

type RequestState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; answer: Answer }
  | { status: "error"; message: string };

export function App() {
  const [state, setState] = useState<RequestState>({ status: "idle" });
  const [token, setToken] = useState<string | null>(null);

  async function handleSubmit(text: string, jurisdictionId: string) {
    setState({ status: "loading" });
    try {
      const answer = await submitQuery({ jurisdictionId, text, token });
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
      <div className="auth">
        {token === null ? (
          <SignInButton onSignIn={setToken} />
        ) : (
          <p className="signed-in">Signed in</p>
        )}
      </div>
      <QueryForm onSubmit={handleSubmit} disabled={state.status === "loading"} />
      {state.status === "error" && <p className="error">{state.message}</p>}
      {state.status === "ready" && <AnswerView answer={state.answer} token={token} />}
    </main>
  );
}
