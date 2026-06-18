"use client";

import type { FormEvent } from "react";
import { useEffect, useRef } from "react";
import { Button, Chip, Form, Input, Surface, Typography } from "@heroui/react";
import {
  categoryLabel,
  formatCurrencyAmount,
  formatRecordDate,
} from "@/features/documents/lib/financial-display";
import type { ChatMessage } from "../types/chat-message";
import type { SupportingRecord } from "../types/assistant";

const suggestedPrompts = [
  "What did I spend the most on this month?",
  "How much did I spend on groceries in May?",
  "Find unpaid bills",
  "Which subscriptions am I paying for?",
];

type DocumentChatProps = {
  messages: ChatMessage[];
  input: string;
  isSending: boolean;
  onInputChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function DocumentChat({
  messages,
  input,
  isSending,
  onInputChange,
  onSubmit,
}: DocumentChatProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Keep the latest message in view as the conversation grows.
  useEffect(() => {
    const container = scrollRef.current;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }, [messages]);

  return (
    <Surface
      render={(props) => <aside {...props} />}
      className="flex min-h-120 w-full flex-1 flex-col bg-white px-5 py-5 sm:px-6 lg:min-h-155 lg:px-8 xl:px-6"
    >
      <Surface variant="transparent">
        <Typography.Heading
          level={2}
          className="text-xl font-semibold text-slate-950"
        >
          Spending assistant
        </Typography.Heading>
        <Typography.Paragraph className="mt-1 text-sm leading-6 text-slate-500">
          Ask about your spending — totals, unpaid bills, subscriptions, and
          summaries, each backed by your records.
        </Typography.Paragraph>
      </Surface>

      <Surface variant="transparent" className="mt-4 flex flex-wrap gap-2">
        {suggestedPrompts.map((prompt) => (
          <Button
            key={prompt}
            type="button"
            variant="outline"
            isDisabled={isSending}
            onPress={() => onInputChange(prompt)}
            className="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-left text-sm font-medium text-slate-600 transition hover:border-indigo-300 hover:text-indigo-700 focus:ring-2 focus:ring-indigo-600 disabled:opacity-50"
          >
            {prompt}
          </Button>
        ))}
      </Surface>

      <Surface
        ref={scrollRef}
        variant="secondary"
        className="mt-5 min-h-0 flex-1 space-y-3 overflow-y-auto rounded-lg border border-slate-200 bg-slate-50 p-3"
      >
        {messages.map((message) => (
          <ChatBubble key={message.id} message={message} />
        ))}
      </Surface>

      <Form onSubmit={onSubmit} className="mt-4 flex gap-2">
        <Input
          id="chat-message"
          aria-label="Ask a spending question"
          value={input}
          disabled={isSending}
          onChange={(event) => onInputChange(event.target.value)}
          placeholder="Ask about totals, bills, or subscriptions"
          className="min-h-11 min-w-0 flex-1 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600 disabled:opacity-60"
        />
        <Button
          type="submit"
          variant="primary"
          aria-label="Send message"
          isDisabled={isSending}
          className="grid min-h-11 shrink-0 place-items-center rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 disabled:opacity-60"
        >
          {isSending ? "…" : "Send"}
        </Button>
      </Form>
    </Surface>
  );
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const isPending = message.status === "pending";
  const isError = message.status === "error";

  return (
    <Surface
      variant="transparent"
      className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}
    >
      <Typography.Paragraph
        className={`max-w-[86%] rounded-lg px-4 py-3 text-sm leading-6 ${
          isUser
            ? "bg-indigo-600 text-white"
            : isError
              ? "border border-rose-200 bg-rose-50 text-rose-700"
              : "border border-slate-200 bg-white text-slate-700"
        } ${isPending ? "animate-pulse text-slate-400" : ""}`}
      >
        {message.text}
      </Typography.Paragraph>

      {message.supportingRecords && message.supportingRecords.length > 0 ? (
        <SupportingRecords records={message.supportingRecords} />
      ) : null}
    </Surface>
  );
}

function SupportingRecords({ records }: { records: SupportingRecord[] }) {
  return (
    <Surface
      variant="transparent"
      className="mt-2 w-full max-w-[86%] space-y-1.5"
    >
      <Typography.Paragraph className="px-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
        Supporting records
      </Typography.Paragraph>
      {records.map((record, index) => (
        <Surface
          key={`${record.upload_id}-${index}`}
          variant="transparent"
          className="flex items-center justify-between gap-3 rounded-md border border-slate-200 bg-white px-3 py-2"
        >
          <Surface variant="transparent" className="min-w-0">
            <Typography.Paragraph className="truncate text-sm font-medium text-slate-800">
              {record.vendor?.trim() || "Unknown vendor"}
            </Typography.Paragraph>
            <Surface
              variant="transparent"
              className="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-slate-500"
            >
              <span>{formatRecordDate(record.date)}</span>
              {record.category ? (
                <Chip
                  size="sm"
                  variant="soft"
                  className="rounded-md bg-indigo-50 text-xs font-semibold text-indigo-700"
                >
                  {categoryLabel(record.category)}
                </Chip>
              ) : null}
            </Surface>
          </Surface>
          {record.amount !== null ? (
            <Typography.Paragraph className="shrink-0 text-sm font-semibold text-slate-950">
              {formatCurrencyAmount(record.amount, "AUD")}
            </Typography.Paragraph>
          ) : null}
        </Surface>
      ))}
    </Surface>
  );
}
