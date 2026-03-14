import streamlit as st

def render_chat_interface(consultant, language="English"):
    """
    Renders the RAG chat interface as a modular component.
    Supports multi-language responses (English, Sheng, French, Swahili).
    """

    # Initialize session state for messages if not present
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask about Kenyan tax laws, licenses, VAT, deductions..."):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            with st.spinner("Consulting regulatory knowledge base..."):
                # Construct context if analysis exists
                context = ""
                if st.session_state.get("analysis_results"):
                    summary = st.session_state.analysis_results.get("summary", "")
                    context = f"Context from current bank statement analysis:\n{summary[:2000]}\n\n"
                
                # Build language instruction
                lang_instruction = f"You MUST respond entirely in {language}."
                if "Sheng" in language:
                    lang_instruction = (
                        "You MUST respond entirely in Sheng - the Kenyan urban slang that mixes "
                        "Swahili, English, and local languages. Use authentic Nairobi street expressions "
                        "like 'maze', 'buda', 'niaje', 'poa', 'keja', 'doh', 'mangaa', etc. "
                        "Keep the tax information accurate but deliver it in a casual, relatable Sheng tone "
                        "like you're explaining to a friend at a kibanda."
                    )
                
                # Query LLM with RAG context + language using fallback logic
                full_prompt = (
                    f"{context}"
                    f"You are a Kenyan Tax Expert. Answer accurately based on Kenyan Law.\n"
                    f"{lang_instruction}\n\n"
                    f"User question: {prompt}"
                )
                response_text = consultant.chat_with_fallback(full_prompt)
                st.markdown(response_text)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response_text})
