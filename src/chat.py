import gradio as gr
from backend import process_message


def chat(user_message: str) -> str:
    return process_message(user_message)


demo = gr.ChatInterface(
    fn=chat,
    title="Cura Agent",
)

if __name__ == "__main__":
    demo.launch()
