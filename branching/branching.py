import streamlit as st
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import numpy as np
import plotly.graph_objects as go
import os
from typing import List, Dict, Any
import json
import uuid

# Initialize Sentence Transformer for embeddings
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Set up Google Gemini API
# api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else os.environ.get("GEMINI_API_KEY")
api_key = "AIzaSyAyBjb3w-583rckUkuvQ9WrZEFxo3NFWhU"
genai.configure(api_key=api_key)

# Initialize Gemini model
gemini_model = genai.GenerativeModel('gemini-1.5-pro')

# Create a simple in-memory vector database
class SimpleVectorDB:
    def __init__(self):
        self.vectors = []
        self.metadata = []
        
    def add(self, text: str, metadata: Dict[str, Any]):
        embedding = embedding_model.encode(text)
        self.vectors.append(embedding)
        self.metadata.append(metadata)
        
    def search(self, query: str, top_k: int = 3):
        if not self.vectors:
            return []
        
        query_embedding = embedding_model.encode(query)
        similarities = [np.dot(query_embedding, vec) / (np.linalg.norm(query_embedding) * np.linalg.norm(vec)) 
                        for vec in self.vectors]
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        results = [{"similarity": similarities[i], "metadata": self.metadata[i]} for i in top_indices]
        
        return results
    
    def clear(self):
        self.vectors = []
        self.metadata = []

# Initialize vector DB in session state
if 'vector_db' not in st.session_state:
    st.session_state.vector_db = SimpleVectorDB()

if 'story_branches' not in st.session_state:
    st.session_state.story_branches = {}

if 'selected_branch_point' not in st.session_state:
    st.session_state.selected_branch_point = None

def preprocess_story(story_text: str):
    """Split story into paragraphs and identify potential branch points"""
    paragraphs = [p.strip() for p in story_text.split('\n') if p.strip()]
    
    # Clear existing DB
    st.session_state.vector_db.clear()
    
    # Add paragraphs to vector DB
    for i, para in enumerate(paragraphs):
        st.session_state.vector_db.add(
            para, 
            {
                "id": str(uuid.uuid4()),
                "type": "paragraph",
                "position": i,
                "text": para
            }
        )
    
    # Generate branch points
    prompt = f"""
    I have a story text. Please identify 3-5 key decision points or moments where the story could branch into different directions.
    For each point, provide:
    1. A brief description of the branching point
    2. The paragraph number where this occurs
    
    Only respond in valid JSON format as follows:
    [
        {{
            "id": "unique_id",
            "description": "Brief description of the branch point",
            "paragraph_index": paragraph_number_where_this_occurs
        }},
        ...
    ]

    Strictly follow the JSON format. Do not add any additional text or explanations. No prefix or suffix of any kind.
    
    Here's the story:
    {story_text}
    """
    
    response = gemini_model.generate_content(prompt)
    # print(response.text)  # Debugging line to check the response
    try:
        branch_points = json.loads(response.text)
        return branch_points
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        st.error("Failed to parse branch points automatically. Please check your story structure.")
        return []

def generate_alternatives(branch_point, story_text, character_info, genre):
    """Generate alternative storylines for a branch point"""
    
    # Get related context from vector DB
    related_paragraphs = st.session_state.vector_db.search(branch_point["description"], top_k=3)
    context = "\n".join([item["metadata"]["text"] for item in related_paragraphs])
    
    prompt = f"""
    Based on this story and the selected branch point, generate 3 alternative story paths.
    
    STORY CONTEXT:
    {context}
    
    BRANCH POINT:
    {branch_point["description"]}
    
    CHARACTER INFORMATION:
    {character_info}
    
    GENRE:
    {genre}
    
    For each alternative path:
    1. Create a title that captures the essence of this path
    2. Write a summary of what happens in this alternative (2-3 sentences)
    3. Generate a sample paragraph showing how the story would continue in this direction
    4. Explain how this maintains character consistency

    Strictly follow the JSON format. Do not add any additional text or explanations. Not even prefix or suffix.
    
    Respond in valid JSON format as follows:
    [
        {{
            "id": "unique_id",
            "title": "Path Title",
            "summary": "Summary of what happens in this path",
            "sample_text": "Sample paragraph of story continuation",
            "character_consistency": "How this maintains character consistency"
        }},
        ...
    ]
    """
    
    response = gemini_model.generate_content(prompt)
    # print("RESPONSE:")
    # print(response.text)  # Debugging line to check the response
    try:
        alternatives = json.loads(response.text)
        return alternatives
    except json.JSONDecodeError:
        st.error("Failed to generate alternatives. Please try again.")
        return []

def create_branch_visualization(branches):
    """Create a visualization of the story branches"""
    if not branches:
        return None
    
    fig = go.Figure()
    
    # Add main trunk
    fig.add_trace(go.Scatter(
        x=[0, 0], 
        y=[0, 1], 
        mode='lines',
        line=dict(color='brown', width=10),
        name='Main Story'
    ))
    
    # Add branches
    colors = ['green', 'blue', 'purple', 'orange', 'red']
    for i, branch in enumerate(branches):
        angle = -45 + (i * 45)
        x_end = np.sin(np.radians(angle)) * 0.8
        y_end = 1 + np.cos(np.radians(angle)) * 0.8
        
        # Draw the branch line
        fig.add_trace(go.Scatter(
            x=[0, x_end], 
            y=[1, y_end], 
            mode='lines',
            line=dict(color=colors[i % len(colors)], width=5),
            showlegend=False
        ))
        
        # Add branch title at the end
        fig.add_trace(go.Scatter(
            x=[x_end], 
            y=[y_end], 
            mode='text',
            text=[branch['title']],
            textposition="middle center",
            showlegend=False
        ))
    
    fig.update_layout(
        title='Story Branching Visualization',
        showlegend=False,
        xaxis=dict(visible=False, range=[-1, 1]),
        yaxis=dict(visible=False, range=[0, 2]),
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='black',  # Optional, but looks clean
        paper_bgcolor='black'
    )
    
    return fig

def main():
    st.title("📝 Writer's Companion: Creative Expansion & Branching")
    st.markdown("Explore alternative story paths and expand your creative possibilities")
    
    with st.sidebar:
        st.header("Story Settings")
        genre = st.selectbox(
            "Select Genre",
            ["Fantasy", "Science Fiction", "Mystery", "Romance", "Thriller", "Historical Fiction"]
        )
        
        st.subheader("Character Information")
        character_info = st.text_area(
            "Provide brief character descriptions",
            "Main character: Sarah - adventurous journalist, 32 years old\n"
            "Supporting character: Marcus - retired detective, skeptical but loyal",
            height=150
        )
    
    story_tab, branch_tab, explore_tab = st.tabs(["Story Input", "Branch Points", "Explore Alternatives"])
    
    with story_tab:
        st.markdown("### Enter your story or outline")
        story_text = st.text_area(
            "Paste your story or detailed outline here",
            "Sarah received a mysterious letter in the mail. It contained coordinates to a location in the mountains and a cryptic message: 'The truth awaits'.\n\n"
            "She debated whether to investigate alone or tell Marcus about it. Marcus had warned her about chasing dangerous leads.\n\n"
            "Sarah decided to call Marcus. He was reluctant but agreed to accompany her.\n\n"
            "They drove to the mountains the next day. The coordinates led to an abandoned research facility.\n\n"
            "At the entrance, they found a keypad requiring a code. Sarah remembered the numbers hidden in the letter.",
            height=300
        )
        
        if st.button("Process Story & Find Branch Points"):
            with st.spinner("Analyzing story structure..."):
                branch_points = preprocess_story(story_text)
                st.session_state.branch_points = branch_points
                st.session_state.story_text = story_text
                st.success(f"Found {len(branch_points)} potential branch points!")
    
    with branch_tab:
        st.markdown("### Select a Point to Branch Your Story")
        
        if 'branch_points' in st.session_state:
            for i, point in enumerate(st.session_state.branch_points):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Branch Point {i+1}:** {point['description']}")
                with col2:
                    if st.button("Select", key=f"select_{i}"):
                        st.session_state.selected_branch_point = point
                        # Generate alternatives when a branch point is selected
                        with st.spinner("Generating alternative story paths..."):
                            alternatives = generate_alternatives(
                                point, 
                                st.session_state.story_text,
                                character_info,
                                genre
                            )
                            st.session_state.story_branches[point['id']] = alternatives
                st.divider()
        else:
            st.info("Process your story first to find branch points")
    
    with explore_tab:
        st.markdown("### Explore Alternative Story Paths")
        
        if st.session_state.selected_branch_point and st.session_state.selected_branch_point['id'] in st.session_state.story_branches:
            selected_point = st.session_state.selected_branch_point
            st.markdown(f"#### Branching from: **{selected_point['description']}**")
            
            alternatives = st.session_state.story_branches[selected_point['id']]
            
            # Visualization
            fig = create_branch_visualization(alternatives)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Show alternatives
            for i, alt in enumerate(alternatives):
                with st.expander(f"Path {i+1}: {alt['title']}"):
                    st.markdown(f"**Summary:** {alt['summary']}")
                    st.markdown("**Sample:**")
                    st.markdown(f"*{alt['sample_text']}*")
                    st.markdown(f"**Character Consistency:** {alt['character_consistency']}")
                    
                    if st.button("Expand This Path", key=f"expand_{i}"):
                        with st.spinner("Developing this story branch..."):
                            expand_prompt = f"""
                            Expand this story branch into a full scene or chapter of approximately 400-500 words.
                            
                            ORIGINAL STORY CONTEXT:
                            {st.session_state.story_text}
                            
                            BRANCH POINT:
                            {selected_point['description']}
                            
                            PATH TO EXPAND:
                            {alt['title']} - {alt['summary']}
                            
                            STARTING TEXT:
                            {alt['sample_text']}
                            
                            CHARACTER INFORMATION:
                            {character_info}
                            
                            GENRE:
                            {genre}
                            
                            Write a compelling and coherent continuation. Focus on maintaining the narrative style,
                            character consistency, and advancing the plot in an engaging way.
                            """
                            
                            expanded_response = gemini_model.generate_content(expand_prompt)
                            st.markdown("### Expanded Story Path")
                            st.markdown(expanded_response.text)
        else:
            st.info("Select a branch point first to explore alternatives")

if __name__ == "__main__":
    main()