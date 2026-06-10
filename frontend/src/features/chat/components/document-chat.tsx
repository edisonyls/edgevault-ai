import type { FormEvent } from "react";
import { IconSend, IconSpark } from "@/components/icons";
import type { ChatMessage } from "../types/chat-message";

const suggestedPrompts = [
  "What was my largest receipt?",
  "List bills due this month",
  "Which files need review?",
];

type DocumentChatProps = {
  messages: ChatMessage[];
  input: string;
  onInputChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function DocumentChat({
  messages,
  input,
  onInputChange,
  onSubmit,
}: DocumentChatProps) {
  return (
    <aside className="flex min-h-[620px] flex-col bg-white px-5 py-5 sm:px-6 lg:px-8 xl:px-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-950">
            Document chat
          </h2>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            Ask questions about uploaded files. Backend wiring can connect here
            later.
          </p>
        </div>
        <div className="grid size-11 shrink-0 place-items-center rounded-md bg-indigo-50 text-indigo-700">
          <IconSpark className="size-5" />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {suggestedPrompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onInputChange(prompt)}
            className="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-left text-sm font-medium text-slate-600 transition hover:border-indigo-300 hover:text-indigo-700 focus:ring-2 focus:ring-indigo-600"
          >
            {prompt}
          </button>
        ))}
      </div>

      <div className="mt-5 min-h-0 flex-1 space-y-3 overflow-y-auto rounded-lg border border-slate-200 bg-slate-50 p-3">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[86%] rounded-lg px-4 py-3 text-sm leading-6 ${
                message.role === "user"
                  ? "bg-indigo-600 text-white"
                  : "border border-slate-200 bg-white text-slate-700"
              }`}
            >
              {message.text}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={onSubmit} className="mt-4 flex gap-2">
        <label className="sr-only" htmlFor="chat-message">
          Ask a document question
        </label>
        <input
          id="chat-message"
          value={input}
          onChange={(event) => onInputChange(event.target.value)}
          placeholder="Ask about totals, vendors, or missing files"
          className="min-h-11 min-w-0 flex-1 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600"
        />
        <button
          type="submit"
          aria-label="Send message"
          className="grid min-h-11 min-w-11 place-items-center rounded-md bg-slate-950 text-white transition hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2"
        >
          <IconSend className="size-5" />
        </button>
      </form>
    </aside>
  );
}
