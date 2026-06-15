import type { FormEvent } from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { askAssistant } from "../api/assistant";
import { initialMessages } from "../data/initial-messages";
import type { ChatMessage } from "../types/chat-message";

type UseDocumentChat = {
  messages: ChatMessage[];
  input: string;
  isSending: boolean;
  setInput: (value: string) => void;
  submit: (event: FormEvent<HTMLFormElement>) => void;
};

/**
 * Drives the document chat against the backend assistant. Each question is
 * answered by the controlled query engine, so every reply is grounded in real
 * records and carries its supporting evidence.
 */
export function useDocumentChat(): UseDocumentChat {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => () => controllerRef.current?.abort(), []);

  const submit = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();

      const question = input.trim();
      if (!question || isSending) {
        return;
      }

      const userId = Date.now();
      const pendingId = userId + 1;

      setMessages((current) => [
        ...current,
        { id: userId, role: "user", text: question },
        {
          id: pendingId,
          role: "assistant",
          text: "Looking through your documents…",
          status: "pending",
        },
      ]);
      setInput("");
      setIsSending(true);

      const controller = new AbortController();
      controllerRef.current = controller;

      askAssistant(question, { signal: controller.signal })
        .then((response) => {
          setMessages((current) =>
            current.map((message) =>
              message.id === pendingId
                ? {
                    id: pendingId,
                    role: "assistant",
                    text: response.answer,
                    queryType: response.query_type,
                    supportingRecords: response.supporting_records,
                  }
                : message,
            ),
          );
        })
        .catch((caught) => {
          if (caught instanceof DOMException && caught.name === "AbortError") {
            return;
          }

          setMessages((current) =>
            current.map((message) =>
              message.id === pendingId
                ? {
                    id: pendingId,
                    role: "assistant",
                    status: "error",
                    text: getErrorMessage(
                      caught,
                      "Sorry, I couldn't answer that just now. Please try again.",
                    ),
                  }
                : message,
            ),
          );
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setIsSending(false);
          }
        });
    },
    [input, isSending],
  );

  return { messages, input, isSending, setInput, submit };
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return fallback;
}
