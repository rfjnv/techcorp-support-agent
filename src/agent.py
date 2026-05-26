import json
import anthropic
from src.rag import RAGPipeline
from src.tickets import GitHubTicketClient

SYSTEM_PROMPT = """You are a Customer Support AI Agent for TechCorp.
Contact information: Phone: +1 800 123 4567, Email: support@techcorp.com

## YOUR TOOLS
1. search_documents(query) — Search the knowledge base for relevant answers
2. create_support_ticket(name, email, summary, description) — Create a GitHub support ticket

## RULES
1. Always search the knowledge base before answering factual questions.
2. Cite sources on every factual answer: "According to [filename], page [X]..."
3. If no answer is found, suggest creating a support ticket.
4. When creating a ticket, collect: full name, email, summary, detailed description.
5. Confirm ticket details with the user before submitting.
6. Never fabricate information — only use what search_documents returns.
7. Keep conversation history in context and reference prior messages when relevant.
8. Be professional, warm, and concise."""

TOOLS = [
    {
        "name": "search_documents",
        "description": "Search the knowledge base documents for relevant information to answer the user's question.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant documents"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_support_ticket",
        "description": "Create a support ticket in GitHub Issues when the user's question cannot be answered from the knowledge base or when the user explicitly requests a ticket.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Customer's full name"},
                "email": {"type": "string", "description": "Customer's email address"},
                "summary": {"type": "string", "description": "Short title/summary of the issue"},
                "description": {"type": "string", "description": "Detailed description of the issue"}
            },
            "required": ["name", "email", "summary", "description"]
        }
    }
]


class SupportAgent:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.rag = RAGPipeline()
        self.tickets = GitHubTicketClient()
        self.history = []

    def reset(self):
        self.history = []

    def _run_tool(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "search_documents":
            results = self.rag.search(tool_input["query"])
            if not results:
                return "No relevant documents found in the knowledge base."
            return json.dumps(results, ensure_ascii=False)

        elif tool_name == "create_support_ticket":
            result = self.tickets.create(
                name=tool_input["name"],
                email=tool_input["email"],
                summary=tool_input["summary"],
                description=tool_input["description"]
            )
            return json.dumps(result)

        return f"Unknown tool: {tool_name}"

    def chat(self, user_message: str, gradio_history: list) -> tuple[str, list]:
        gradio_history = list(gradio_history)
        gradio_history.append({"role": "user", "content": user_message})
        self.history.append({"role": "user", "content": user_message})

        while True:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.history
            )

            self.history.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                text = next(
                    (block.text for block in response.content if hasattr(block, "text")),
                    "I'm sorry, I couldn't generate a response."
                )
                gradio_history.append({"role": "assistant", "content": text})
                return "", gradio_history

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._run_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })
                self.history.append({"role": "user", "content": tool_results})
                continue

            gradio_history.append({
                "role": "assistant",
                "content": "Something went wrong. Please try again."
            })
            return "", gradio_history
