import type { ChatMessage } from "../types/chat-message";

export const initialMessages: ChatMessage[] = [
  {
    id: 1,
    role: "assistant",
    text: "Ask me about your spending — totals by category, unpaid bills, subscriptions, or a summary for a month. Every answer is backed by the records it came from.",
  },
];
