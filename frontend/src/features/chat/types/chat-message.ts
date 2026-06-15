import type { AssistantQueryType, SupportingRecord } from "./assistant";

export type ChatMessage = {
  id: number;
  role: "assistant" | "user";
  text: string;
  status?: "pending" | "error";
  queryType?: AssistantQueryType;
  supportingRecords?: SupportingRecord[];
};
