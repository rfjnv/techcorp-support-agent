import gradio as gr
from src.agent import SupportAgent

_agent = None


def get_agent() -> SupportAgent:
    global _agent
    if _agent is None:
        _agent = SupportAgent()
    return _agent

def chat(message, history):
    _, history = get_agent().chat(message, history)
    return "", history


def reset():
    get_agent().reset()
    return []

with gr.Blocks(
    title="TechCorp Support",
    theme=gr.themes.Soft(primary_hue="blue"),
    css="""
    #chatbot { height: 520px; }
    .footer-info { text-align: center; color: #888; font-size: 0.85rem; margin-top: 8px; }
    """
) as demo:
    gr.Markdown("# 🤖 TechCorp Customer Support\n*Powered by RAG + Claude AI*")

    chatbot = gr.Chatbot(elem_id="chatbot", type="messages", show_label=False)
    
    with gr.Row():
        msg = gr.Textbox(
            placeholder="Ask a question or describe your issue...",
            show_label=False,
            scale=9
        )
        send_btn = gr.Button("Send", variant="primary", scale=1)

    with gr.Row():
        clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary")

    gr.Markdown(
        "📞 +1 800 123 4567 &nbsp;|&nbsp; ✉️ support@techcorp.com",
        elem_classes="footer-info"
    )

    # Events
    msg.submit(chat, [msg, chatbot], [msg, chatbot])
    send_btn.click(chat, [msg, chatbot], [msg, chatbot])
    clear_btn.click(reset, outputs=[chatbot])

    # Greet on load
    demo.load(
        lambda: [{"role": "assistant", "content": (
            "Hello! I'm **TechCorp**'s support assistant.\n\n"
            "📞 **Phone:** +1 800 123 4567\n"
            "✉️ **Email:** support@techcorp.com\n\n"
            "I can answer questions from our knowledge base (with document citations) "
            "and open a GitHub support ticket if needed.\n\n"
            "What can I help you with today?"
        )}],
        outputs=[chatbot]
    )

demo.queue().launch(
    server_name="0.0.0.0",
    server_port=7860,
    show_api=False,
)
