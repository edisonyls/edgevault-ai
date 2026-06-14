import type { FormEvent } from "react";
import { Button, Form, Input, Surface, Typography } from "@heroui/react";
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
    <Surface
      render={(props) => <aside {...props} />}
      className="flex min-h-[480px] flex-col bg-white px-5 py-5 sm:px-6 lg:min-h-[620px] lg:px-8 xl:px-6"
    >
      <Surface variant="transparent">
        <Typography.Heading
          level={2}
          className="text-xl font-semibold text-slate-950"
        >
          Document chat
        </Typography.Heading>
        <Typography.Paragraph className="mt-1 text-sm leading-6 text-slate-500">
          Ask questions about your uploaded files — totals, vendors, due dates,
          and more.
        </Typography.Paragraph>
      </Surface>

      <Surface variant="transparent" className="mt-4 flex flex-wrap gap-2">
        {suggestedPrompts.map((prompt) => (
          <Button
            key={prompt}
            type="button"
            variant="outline"
            onPress={() => onInputChange(prompt)}
            className="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-left text-sm font-medium text-slate-600 transition hover:border-indigo-300 hover:text-indigo-700 focus:ring-2 focus:ring-indigo-600"
          >
            {prompt}
          </Button>
        ))}
      </Surface>

      <Surface
        variant="secondary"
        className="mt-5 min-h-0 flex-1 space-y-3 overflow-y-auto rounded-lg border border-slate-200 bg-slate-50 p-3"
      >
        {messages.map((message) => (
          <Surface
            key={message.id}
            variant="transparent"
            className={`flex ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <Typography.Paragraph
              className={`max-w-[86%] rounded-lg px-4 py-3 text-sm leading-6 ${
                message.role === "user"
                  ? "bg-indigo-600 text-white"
                  : "border border-slate-200 bg-white text-slate-700"
              }`}
            >
              {message.text}
            </Typography.Paragraph>
          </Surface>
        ))}
      </Surface>

      <Form onSubmit={onSubmit} className="mt-4 flex gap-2">
        <Input
          id="chat-message"
          aria-label="Ask a document question"
          value={input}
          onChange={(event) => onInputChange(event.target.value)}
          placeholder="Ask about totals, vendors, or missing files"
          className="min-h-11 min-w-0 flex-1 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600"
        />
        <Button
          type="submit"
          variant="primary"
          aria-label="Send message"
          className="grid min-h-11 shrink-0 place-items-center rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2"
        >
          Send
        </Button>
      </Form>
    </Surface>
  );
}
