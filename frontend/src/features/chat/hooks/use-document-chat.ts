import type { FormEvent } from "react";
import { useState } from "react";
import { sumDetectedAmounts } from "@/features/documents/lib/document-utils";
import type { VaultDocument } from "@/features/documents/types/document";
import { initialMessages } from "../data/mock-messages";
import type { ChatMessage } from "../types/chat-message";

type UseDocumentChat = {
  messages: ChatMessage[];
  input: string;
  setInput: (value: string) => void;
  submit: (event: FormEvent<HTMLFormElement>) => void;
};

/**
 * Holds the (currently mocked) document chat conversation and produces a
 * preview answer derived from the live document collection.
 */
export function useDocumentChat(documents: VaultDocument[]): UseDocumentChat {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const question = input.trim();

    if (!question) {
      return;
    }

    const reviewCount = documents.filter(
      (document) => document.status === "Review",
    ).length;
    const totalAmount = sumDetectedAmounts(documents);

    setMessages((current) => [
      ...current,
      { id: Date.now(), role: "user", text: question },
      {
        id: Date.now() + 1,
        role: "assistant",
        text: `Preview answer: I found ${documents.length} uploaded documents, ${reviewCount} marked for review, and about $${totalAmount.toFixed(
          2,
        )} across documents with detected totals.`,
      },
    ]);
    setInput("");
  }

  return { messages, input, setInput, submit };
}
