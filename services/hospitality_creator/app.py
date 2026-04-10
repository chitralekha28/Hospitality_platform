import os

import chromadb
import streamlit as st
import torch
from chromadb.config import Settings
from diffusers import StableDiffusionPipeline
from dotenv import load_dotenv
from google import genai
from sentence_transformers import SentenceTransformer

load_dotenv()

SESSION_PREFIX = "hospitality_creator_"
_RESOURCES = {}

DOCUMENTS = [
    """
    Eco resorts integrate local materials like volcanic stone,
    passive cooling strategies, and open-air pavilions to enhance
    natural ventilation and climate harmony.
    """,
    """
    Sustainable hospitality architecture includes rainwater harvesting,
    solar integration, geothermal systems, and visible sustainability
    elements as part of aesthetic identity.
    """,
    """
    Cliffside resorts use terraced structural planning,
    cascading platforms, and infinity pools aligned with natural horizons.
    """,
    """
    Biophilic design blends indoor and outdoor spaces through
    green walls, courtyards, natural light, and organic materials.
    """,
]


def _state_key(name: str) -> str:
    return f"{SESSION_PREFIX}{name}"


def _ensure_session_state() -> None:
    defaults = {
        "status": "",
        "enhanced": "",
        "narrative": "",
        "images": [],
    }
    for key, value in defaults.items():
        session_key = _state_key(key)
        if session_key not in st.session_state:
            st.session_state[session_key] = value


def _get_api_key() -> str:
    return os.getenv("GOOGLE_API_KEY", "").strip()


def _get_resources():
    if _RESOURCES:
        return _RESOURCES

    api_key = _get_api_key()
    if not api_key:
        raise ValueError("Please set GOOGLE_API_KEY as environment variable.")

    client = genai.Client(api_key=api_key)
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    chroma_client = chromadb.Client(Settings())
    collection = chroma_client.get_or_create_collection("hospitality_docs")

    if collection.count() == 0:
        for index, doc in enumerate(DOCUMENTS):
            embedding = embedding_model.encode(doc).tolist()
            collection.add(documents=[doc], embeddings=[embedding], ids=[str(index)])

    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )
    if torch.cuda.is_available():
        pipe = pipe.to("cuda")

    _RESOURCES.update(
        {
            "client": client,
            "embedding_model": embedding_model,
            "collection": collection,
            "pipe": pipe,
        }
    )
    return _RESOURCES


def retrieve_context(query: str) -> str:
    resources = _get_resources()
    query_embedding = resources["embedding_model"].encode(query).tolist()
    results = resources["collection"].query(query_embeddings=[query_embedding], n_results=3)
    return "\n".join(results["documents"][0])


def enhance_prompt(user_prompt: str, context: str) -> str:
    resources = _get_resources()
    prompt = f"""
    You are a hospitality architecture expert.

    Context:
    {context}

    Enhance this concept into a cinematic architectural visualization prompt:

    {user_prompt}
    """

    response = resources["client"].models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt,
    )
    return response.text


def generate_narrative(enhanced_prompt: str) -> str:
    resources = _get_resources()
    prompt = f"""
    Write a professional hospitality project description:

    {enhanced_prompt}
    """

    response = resources["client"].models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt,
    )
    return response.text


def generate_images(enhanced_prompt: str):
    resources = _get_resources()
    base_prompt = """
    ultra realistic architectural photography,
    luxury eco resort building clearly visible,
    modern minimal desert architecture,
    rammed earth walls,
    shaded courtyards,
    infinity pool,
    glass facade,
    large resort structure in foreground,
    sand dunes in background,
    professional architectural render,
    sharp focus, 8k
    """

    negative_prompt = """
    empty desert, landscape only,
    no building, no architecture,
    surreal, distorted, blurry
    """

    views = [
        "aerial drone shot showing full resort complex",
        "eye level facade view of resort entrance",
        "wide angle shot showing resort integrated with dunes",
        "poolside perspective looking toward building",
    ]

    images = []
    for view in views:
        full_prompt = f"""
        {enhanced_prompt},

        {base_prompt},

        Camera perspective: {view}
        """
        image = resources["pipe"](
            full_prompt,
            negative_prompt=negative_prompt,
            guidance_scale=9.5,
            num_inference_steps=40,
        ).images[0]
        images.append(image)
    return images


def render_app() -> None:
    _ensure_session_state()

    st.markdown("# Multimodal Hospitality Creator")
    st.markdown("AI-powered hospitality concept visualization using RAG + Gemini + Stable Diffusion")

    if not _get_api_key():
        st.warning("GOOGLE_API_KEY is not set. Add it to your .env file to use this section.")
        return

    user_input = st.text_area(
        "Enter Your Hospitality Concept",
        height=100,
        placeholder="A luxury desert eco resort with sand dunes...",
        key=_state_key("user_input"),
    )

    generate_btn = st.button("Generate Concept", key=_state_key("generate_btn"))

    if generate_btn:
        if not user_input.strip():
            st.warning("Please enter a hospitality concept first.")
        else:
            try:
                with st.spinner("Retrieving architectural knowledge..."):
                    context = retrieve_context(user_input)

                with st.spinner("Enhancing cinematic prompt..."):
                    enhanced = enhance_prompt(user_input, context)

                with st.spinner("Generating professional narrative..."):
                    narrative = generate_narrative(enhanced)

                with st.spinner("Rendering architectural visuals..."):
                    images = generate_images(enhanced)

                st.session_state[_state_key("status")] = "Concept generated successfully."
                st.session_state[_state_key("enhanced")] = enhanced
                st.session_state[_state_key("narrative")] = narrative
                st.session_state[_state_key("images")] = images
            except Exception as exc:
                st.session_state[_state_key("status")] = f"Generation failed: {exc}"
                st.session_state[_state_key("enhanced")] = ""
                st.session_state[_state_key("narrative")] = ""
                st.session_state[_state_key("images")] = []

    if st.session_state[_state_key("status")]:
        st.markdown(st.session_state[_state_key("status")])

    prompt_tab, narrative_tab, views_tab = st.tabs(
        ["Enhanced Cinematic Prompt", "Project Narrative", "Generated Views"]
    )

    with prompt_tab:
        if st.session_state[_state_key("enhanced")]:
            st.markdown(st.session_state[_state_key("enhanced")])
        else:
            st.info("Your enhanced cinematic prompt will appear here.")

    with narrative_tab:
        if st.session_state[_state_key("narrative")]:
            st.markdown(st.session_state[_state_key("narrative")])
        else:
            st.info("Your hospitality project narrative will appear here.")

    with views_tab:
        images = st.session_state[_state_key("images")]
        if images:
            columns = st.columns(2)
            for index, image in enumerate(images):
                columns[index % 2].image(image, use_container_width=True)
        else:
            st.info("Generated resort views will appear here.")


if __name__ == "__main__":
    st.set_page_config(page_title="Multimodal Hospitality Creator", layout="wide")
    render_app()
