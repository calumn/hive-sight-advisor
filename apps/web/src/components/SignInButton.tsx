import { useEffect, useRef } from "react";
import { loadGoogleIdentityServices } from "../auth/googleSignIn";

export type SignInButtonProps = {
  onSignIn: (token: string) => void;
};

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "";

export function SignInButton({ onSignIn }: SignInButtonProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) {
      return;
    }
    let cancelled = false;

    loadGoogleIdentityServices().then(() => {
      if (cancelled || containerRef.current === null || window.google === undefined) {
        return;
      }
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: (response) => onSignIn(response.credential)
      });
      window.google.accounts.id.renderButton(containerRef.current, {
        theme: "outline",
        size: "medium"
      });
    });

    return () => {
      cancelled = true;
    };
  }, [onSignIn]);

  if (!GOOGLE_CLIENT_ID) {
    return <p className="sign-in-unavailable">Sign-in is not configured yet.</p>;
  }

  return <div ref={containerRef} className="sign-in-button" />;
}
