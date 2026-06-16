"use client";

import {
  createContext,
  type FormEvent,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Button, Surface, Typography } from "@heroui/react";
import {
  getSession,
  login,
  logout,
  type WorkspaceKey,
  type WorkspaceSession,
} from "../api/auth";

type AuthContextValue = {
  session: WorkspaceSession;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

type AuthGateProps = {
  children: ReactNode;
};

export function AuthGate({ children }: AuthGateProps) {
  const [session, setSession] = useState<WorkspaceSession | null>(null);
  const [isChecking, setIsChecking] = useState(true);

  const signOut = useCallback(async () => {
    await logout();
    setSession({ authenticated: false, workspace: null });
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function loadSession() {
      try {
        setSession(await getSession({ signal: controller.signal }));
      } catch {
        setSession({ authenticated: false, workspace: null });
      } finally {
        if (!controller.signal.aborted) {
          setIsChecking(false);
        }
      }
    }

    void loadSession();

    return () => controller.abort();
  }, []);

  useEffect(() => {
    function handleUnauthorized() {
      setSession({ authenticated: false, workspace: null });
    }

    window.addEventListener("edgevault:unauthorized", handleUnauthorized);
    return () =>
      window.removeEventListener("edgevault:unauthorized", handleUnauthorized);
  }, []);

  const contextValue = useMemo(
    () => (session ? { session, signOut } : null),
    [session, signOut],
  );

  if (isChecking || session === null) {
    return <AuthShell title="EdgeVault AI" subtitle="Checking workspace..." />;
  }

  if (!session.authenticated || session.workspace === null) {
    return <LoginScreen onAuthenticated={setSession} />;
  }

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (value === null) {
    throw new Error("useAuth must be used inside AuthGate.");
  }
  return value;
}

function LoginScreen({
  onAuthenticated,
}: {
  onAuthenticated: (session: WorkspaceSession) => void;
}) {
  const [workspace, setWorkspace] = useState<WorkspaceKey>("owner");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const nextSession = await login(workspace, password);
      onAuthenticated(nextSession);
      setPassword("");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Could not unlock workspace.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthShell title="EdgeVault AI" subtitle="Unlock workspace">
      <form onSubmit={handleSubmit} className="mt-8 space-y-5">
        <fieldset>
          <legend className="mb-2 text-sm font-medium text-slate-700">
            Workspace
          </legend>
          <div className="grid grid-cols-2 rounded-md border border-slate-200 bg-slate-100 p-1">
            {(["owner", "demo"] as const).map((key) => (
              <button
                key={key}
                type="button"
                aria-pressed={workspace === key}
                onClick={() => setWorkspace(key)}
                className={`min-h-10 rounded px-3 text-sm font-semibold transition ${
                  workspace === key
                    ? "bg-white text-slate-950 shadow-sm"
                    : "text-slate-600 hover:text-slate-950"
                }`}
              >
                {key === "owner" ? "Personal" : "Demo"}
              </button>
            ))}
          </div>
        </fieldset>

        <label className="block text-sm font-medium text-slate-700">
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            className="mt-2 min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 text-base text-slate-950 outline-none transition focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100"
            required
          />
        </label>

        {error && (
          <Typography.Paragraph
            role="alert"
            className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700"
          >
            {error}
          </Typography.Paragraph>
        )}

        <Button
          type="submit"
          variant="primary"
          isDisabled={isSubmitting}
          className="min-h-11 w-full rounded-md bg-indigo-600 text-sm font-semibold text-white transition hover:bg-indigo-700 focus-visible:ring-2 focus-visible:ring-indigo-600 focus-visible:ring-offset-2"
        >
          {isSubmitting ? "Unlocking..." : "Unlock"}
        </Button>
      </form>
    </AuthShell>
  );
}

function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children?: ReactNode;
}) {
  return (
    <main className="grid min-h-screen place-items-center bg-[#f7f8fb] px-4 py-10 text-slate-950">
      <Surface className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="grid size-10 shrink-0 place-items-center rounded-md bg-slate-950 text-sm font-bold tracking-tight text-white">
            EV
          </div>
          <div>
            <Typography.Heading
              level={1}
              className="text-xl font-semibold tracking-tight"
            >
              {title}
            </Typography.Heading>
            <Typography.Paragraph className="text-sm text-slate-500">
              {subtitle}
            </Typography.Paragraph>
          </div>
        </div>
        {children}
      </Surface>
    </main>
  );
}
